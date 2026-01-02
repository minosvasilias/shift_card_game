"""Agent that looks ahead n turns using minimax search."""

from __future__ import annotations

import random
from typing import Any

from game.state import (
    GameState,
    PlayAction,
    DrawChoice,
    EffectChoice,
    Side,
    CardType,
)
from game.engine import GameEngine
from .base import Agent
from .greedy_agent import GreedyAgent


class LookaheadAgent(Agent):
    """
    Agent that simulates n turns ahead using minimax-style search.

    Uses a greedy opponent model to predict opponent moves and evaluates
    game states at depth n based on score differential.
    """

    def __init__(self, seed: int | None = None, depth: int = 2):
        """
        Initialize the lookahead agent.

        Args:
            seed: Optional random seed for tiebreaking
            depth: Number of turns to look ahead (default: 2)
        """
        self.rng = random.Random(seed)
        self.depth = max(1, depth)  # Minimum depth of 1
        self.greedy = GreedyAgent(seed)  # For opponent modeling and fallback

    def choose_action(self, state: GameState, player_idx: int) -> PlayAction:
        """Evaluate all possible plays using lookahead and pick the best one."""
        player = state.players[player_idx]
        hand = player.hand

        if not hand:
            return PlayAction(hand_index=0, side=Side.LEFT)

        best_action = None
        best_score = float('-inf')
        ties = []

        # Evaluate each possible action
        for hand_idx, card in enumerate(hand):
            for side in [Side.LEFT, Side.RIGHT]:
                # For traps, evaluate both face-up and face-down
                face_down_options = [False]
                if card.card_type == CardType.TRAP:
                    face_down_options = [True, False]

                for face_down in face_down_options:
                    action = PlayAction(
                        hand_index=hand_idx,
                        side=side,
                        face_down=face_down,
                    )

                    # Evaluate this action with lookahead
                    score = self._evaluate_action_lookahead(
                        state, player_idx, action, self.depth
                    )

                    if score > best_score:
                        best_score = score
                        best_action = action
                        ties = [action]
                    elif score == best_score:
                        ties.append(action)

        # Break ties randomly
        if ties:
            return self.rng.choice(ties)
        return best_action or PlayAction(hand_index=0, side=Side.LEFT)

    def _evaluate_action_lookahead(
        self,
        state: GameState,
        player_idx: int,
        action: PlayAction,
        depth: int,
    ) -> float:
        """
        Evaluate an action by simulating gameplay to a given depth.

        Args:
            state: Current game state
            player_idx: Player making the action
            action: Action to evaluate
            depth: Number of turns to look ahead

        Returns:
            Expected score differential after depth turns
        """
        # Create a copy of the game state
        sim_state = state.copy()

        # Validate action
        sim_player = sim_state.players[player_idx]
        if action.hand_index >= len(sim_player.hand):
            # Invalid action
            return float('-inf')

        # Simulate the action on the copied state
        try:
            sim_state = self._simulate_action(sim_state, player_idx, action)
        except (IndexError, AttributeError, KeyError):
            # Invalid action
            return float('-inf')

        # Now recursively evaluate remaining depth
        return self._minimax_simple(sim_state, player_idx, depth - 1)

    def _minimax_simple(
        self,
        state: GameState,
        player_idx: int,
        depth: int,
    ) -> float:
        """
        Simple minimax evaluation without full game engine.

        Args:
            state: Current game state
            player_idx: The player we're maximizing for
            depth: Remaining depth to search

        Returns:
            Evaluated score for the position
        """
        # Terminal conditions
        if depth <= 0 or state.game_over:
            return self._evaluate_state(state, player_idx)

        current_idx = state.current_player

        # If it's our turn to move, maximize
        if current_idx == player_idx:
            max_eval = float('-inf')

            # Try all possible actions
            player = state.players[player_idx]
            if not player.hand:
                # No cards to play, skip to opponent's turn
                state_copy = state.copy()
                state_copy.current_player = 1 - player_idx
                return self._minimax_simple(state_copy, player_idx, depth - 1)

            for hand_idx, card in enumerate(player.hand):
                for side in [Side.LEFT, Side.RIGHT]:
                    face_down_options = [False]
                    if card.card_type == CardType.TRAP:
                        face_down_options = [True, False]

                    for face_down in face_down_options:
                        action = PlayAction(hand_idx, side, face_down)

                        # Simulate this action
                        try:
                            new_state = self._simulate_action(state, player_idx, action)
                            eval_score = self._minimax_simple(new_state, player_idx, depth - 1)
                            max_eval = max(max_eval, eval_score)
                        except (IndexError, AttributeError, KeyError):
                            # Invalid action, skip
                            continue

            return max_eval if max_eval != float('-inf') else self._evaluate_state(state, player_idx)

        else:  # Opponent's turn
            # Use greedy agent to pick opponent's move
            action = self.greedy.choose_action(state, current_idx)

            # Simulate opponent's action
            try:
                new_state = self._simulate_action(state, current_idx, action)
                return self._minimax_simple(new_state, player_idx, depth - 1)
            except (IndexError, AttributeError, KeyError):
                return self._evaluate_state(state, player_idx)

    def _simulate_action(
        self,
        state: GameState,
        player_idx: int,
        action: PlayAction,
    ) -> GameState:
        """
        Simulate an action on a game state (returns new state copy).

        Uses comprehensive scoring estimation matching greedy agent's evaluation.
        """
        from game.state import CardInPlay

        # Create a copy of the state
        new_state = state.copy()
        player = new_state.players[player_idx]

        # Remove card from hand
        if action.hand_index >= len(player.hand):
            raise IndexError("Invalid hand index")

        card = player.hand.pop(action.hand_index)
        card_in_play = CardInPlay(card=card, face_up=not action.face_down)

        # Add card to row and track if a card was pushed out
        pushed_card = None
        if action.side == Side.LEFT:
            player.row.insert(0, card_in_play)
            if len(player.row) > 3:
                pushed_card = player.row.pop()  # Push out right card
        else:
            player.row.append(card_in_play)
            if len(player.row) > 3:
                pushed_card = player.row.pop(0)  # Push out left card

        # Evaluate exit effect if a card was pushed
        if pushed_card and pushed_card.face_up:
            if pushed_card.card.card_type == CardType.EXIT:
                exit_score = self.greedy._estimate_exit_score(
                    pushed_card, new_state, player_idx
                )
                player.score += int(exit_score)

        # Evaluate center trigger
        if len(player.row) == 3:
            center = player.row[1]
            if center.face_up and center.card.card_type == CardType.CENTER:
                # Estimate center score
                estimated_score = self.greedy._estimate_center_score(
                    center, player.row, new_state, player_idx
                )
                player.score += int(estimated_score)

        # Use greedy's draw logic to choose deck vs market
        draw_choice = self.greedy.choose_draw(new_state, player_idx)

        if draw_choice == DrawChoice.MARKET and new_state.market:
            # Pick best card from market using greedy's logic
            best_idx = 0
            best_value = float('-inf')
            for idx, market_card in enumerate(new_state.market):
                value = self.greedy._card_value(market_card, new_state, player_idx)
                if value > best_value:
                    best_value = value
                    best_idx = idx
            if best_idx < len(new_state.market):
                player.hand.append(new_state.market.pop(best_idx))
        elif new_state.deck:
            player.hand.append(new_state.deck.pop())

        # Advance to next player
        new_state.current_player = 1 - player_idx
        if new_state.current_player == 0:
            new_state.turn_counter += 1

        return new_state

    def _evaluate_state(self, state: GameState, player_idx: int) -> float:
        """
        Evaluate a game state from the perspective of player_idx.

        Returns the score differential (our score - opponent score) plus
        some positional bonuses.
        """
        our_score = state.players[player_idx].score
        opp_score = state.players[1 - player_idx].score

        # Base evaluation: score differential
        eval_score = our_score - opp_score

        # Small bonus for cards in hand (flexibility)
        our_hand_size = len(state.players[player_idx].hand)
        opp_hand_size = len(state.players[1 - player_idx].hand)
        eval_score += 0.1 * (our_hand_size - opp_hand_size)

        # Small bonus for cards in row (potential points)
        our_row_size = len(state.players[player_idx].row)
        opp_row_size = len(state.players[1 - player_idx].row)
        eval_score += 0.05 * (our_row_size - opp_row_size)

        return eval_score

    def choose_draw(self, state: GameState, player_idx: int) -> DrawChoice:
        """Delegate to greedy agent for draw choices."""
        return self.greedy.choose_draw(state, player_idx)

    def choose_effect_option(
        self, state: GameState, player_idx: int, choice: EffectChoice
    ) -> Any:
        """Delegate to greedy agent for effect choices."""
        return self.greedy.choose_effect_option(state, player_idx, choice)
