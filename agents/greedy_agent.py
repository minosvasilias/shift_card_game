"""Greedy agent that picks the highest immediate value move."""

from __future__ import annotations

import random
from typing import Any

from game.state import (
    GameState,
    PlayerState,
    CardInPlay,
    PlayAction,
    DrawChoice,
    EffectChoice,
    Side,
    CardType,
    Icon,
)
from .base import Agent


class GreedyAgent(Agent):
    """
    Agent that evaluates each possible move and picks the highest immediate value.

    Evaluation considers:
    - Points scored from center triggers
    - Points scored from exit effects (when pushing cards out)
    - Points given to opponent (negative)
    - Simple heuristics for card positioning
    """

    def __init__(self, seed: int | None = None):
        """
        Initialize the greedy agent.

        Args:
            seed: Optional random seed for tiebreaking
        """
        self.rng = random.Random(seed)

    def choose_action(self, state: GameState, player_idx: int) -> PlayAction:
        """Evaluate all possible plays and pick the best one."""
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
                    score = self._evaluate_action(state, player_idx, action)

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

    def _evaluate_action(
        self, state: GameState, player_idx: int, action: PlayAction
    ) -> float:
        """
        Evaluate the immediate value of an action.

        Returns a score representing the net benefit of this action.
        """
        player = state.players[player_idx]
        opponent_idx = 1 - player_idx
        card = player.hand[action.hand_index]

        # Simulate the play
        new_row = list(player.row)
        card_in_play = CardInPlay(card=card, face_up=not action.face_down)

        # Add card to row
        pushed_card = None
        if action.side == Side.LEFT:
            new_row.insert(0, card_in_play)
            if len(new_row) > 3:
                pushed_card = new_row.pop()
        else:
            new_row.append(card_in_play)
            if len(new_row) > 3:
                pushed_card = new_row.pop(0)

        score = 0.0

        # Evaluate center trigger (only with exactly 3 cards)
        if len(new_row) == 3:
            center_card = new_row[1]
            if center_card.face_up and center_card.card.card_type == CardType.CENTER:
                score += self._estimate_center_score(
                    center_card, new_row, state, player_idx
                )

        # Evaluate exit effect if a card was pushed
        if pushed_card and pushed_card.face_up:
            if pushed_card.card.card_type == CardType.EXIT:
                score += self._estimate_exit_score(pushed_card, state, player_idx)

        # Bonus for playing traps face-down (hidden information value)
        if action.face_down:
            score += 0.5

        # Penalty for cards that give opponent points
        if card.name == "Siphon Drone":
            score -= 1  # Opponent gets 2, but we get 3, net is still positive

        # Small bonus for diverse icons (helps Sequence Bot later)
        if not action.face_down and card.icon:
            existing_icons = {c.card.icon for c in player.row if c.face_up and c.card.icon}
            if card.icon not in existing_icons:
                score += 0.3

        return score

    def _estimate_center_score(
        self,
        center_card: CardInPlay,
        row: list[CardInPlay],
        state: GameState,
        player_idx: int,
    ) -> float:
        """Estimate points from a center trigger without fully simulating."""
        card = center_card.card
        name = card.name

        # Simple scoring cards
        if name == "Calibration Unit":
            return 2
        elif name == "Siphon Drone":
            return 3 - 2  # We get 3, opponent gets 2
        elif name == "One-Shot":
            return 5
        elif name == "Echo Chamber":
            return 4 if state.turn_counter % 2 == 0 else 0
        elif name == "Hot Potato":
            return 2
        elif name == "Embargo":
            return 1
        elif name == "Magnet":
            return 1
        elif name == "Kickback":
            return 2
        elif name == "Turncoat":
            return 2
        elif name == "Scavenger":
            return 0
        elif name == "Hollow Frame":
            return 0
        elif name == "Patience Circuit":
            # Estimate based on remaining turns
            remaining = (10 - state.turn_counter) * 2
            return remaining * 0.3  # Rough estimate

        # Adjacency-based cards
        elif name == "Loner Bot":
            left_icons = row[0].effective_icons if row[0].face_up else set()
            right_icons = row[2].effective_icons if row[2].face_up else set()
            center_icons = center_card.effective_icons
            if (left_icons & center_icons) or (right_icons & center_icons):
                return 0
            return 4

        elif name == "Sequence Bot":
            icons = set()
            for c in row:
                if c.face_up:
                    icons |= c.effective_icons
            return 3 if len(icons) == 3 else 1

        elif name == "Buddy System":
            # This triggers when there are 3 cards, but scores only if 2 cards
            # So it would score 0 when triggered as center
            return 0

        elif name == "Jealous Unit":
            opponent_row = state.players[1 - player_idx].row
            center_icons = center_card.effective_icons
            count = sum(1 for c in opponent_row if c.effective_icons & center_icons)
            return 2 * count

        elif name == "Copycat":
            # Would need to track last scores - estimate conservatively
            return 1

        elif name == "Mimic":
            return 2

        elif name == "Tug-of-War":
            return 1  # Updated from design: scores 1

        elif name == "Void":
            empty_slots = (3 - len(state.players[0].row)) + (3 - len(state.players[1].row))
            # After this play, our row is full (3), so only count opponent's empty
            empty_after = 3 - len(state.players[1 - player_idx].row)
            return 2 * empty_after

        # Default
        return 1

    def _estimate_exit_score(
        self,
        card: CardInPlay,
        state: GameState,
        player_idx: int,
    ) -> float:
        """Estimate points from an exit effect."""
        name = card.card.name

        if name == "Farewell Unit":
            return 3
        elif name == "Sacrificial Lamb":
            return 3
        elif name == "Spite Module":
            return 0.5  # Disrupts opponent
        elif name == "Boomerang":
            return 0.5  # Returns to hand, can be useful
        elif name == "Donation Bot":
            return -0.5  # Goes to opponent's hand
        elif name == "Rewinder":
            return 0.5  # Gets a card from market

        return 0

    def choose_draw(self, state: GameState, player_idx: int) -> DrawChoice:
        """Choose where to draw from based on card value."""
        has_embargo = state.has_embargo(player_idx)
        can_draw_market = bool(state.market) and not has_embargo
        can_draw_deck = bool(state.deck)

        if not can_draw_market:
            return DrawChoice.DECK
        if not can_draw_deck:
            return DrawChoice.MARKET

        # Evaluate market cards
        best_market_value = max(
            self._card_value(card, state, player_idx)
            for card in state.market
        ) if state.market else 0

        # Unknown deck card - estimate average value
        deck_value = 1.5

        if best_market_value > deck_value:
            return DrawChoice.MARKET
        elif best_market_value < deck_value:
            return DrawChoice.DECK
        else:
            return self.rng.choice([DrawChoice.DECK, DrawChoice.MARKET])

    def _card_value(self, card, state: GameState, player_idx: int) -> float:
        """Estimate the general value of having a card."""
        name = card.name

        # High value cards
        if name in ["One-Shot", "Calibration Unit", "Echo Chamber"]:
            return 3
        elif name in ["Farewell Unit", "Sacrificial Lamb"]:
            return 2.5
        elif name in ["Loner Bot", "Sequence Bot"]:
            return 2
        elif name in ["Siphon Drone", "Kickback", "Magnet"]:
            return 1.5

        # Traps have hidden value
        if card.card_type == CardType.TRAP:
            return 2

        # Low value / situational
        if name in ["Hollow Frame", "Scavenger", "Void"]:
            return 0.5
        if name in ["Donation Bot", "Hot Potato"]:
            return 0.5

        return 1

    def choose_effect_option(
        self, state: GameState, player_idx: int, choice: EffectChoice
    ) -> Any:
        """Make choices for card effects."""
        if not choice.options:
            return None

        choice_type = choice.choice_type

        # For Kickback, prefer pushing toward the side with a card to push out
        if choice_type == "kickback_direction":
            row = state.players[player_idx].row
            # Evaluate which direction pushes out a less valuable card
            left_value = self._card_value(row[0].card, state, player_idx) if row else 0
            right_value = self._card_value(row[-1].card, state, player_idx) if row else 0

            if Side.RIGHT in choice.options and Side.LEFT in choice.options:
                # Push toward the side with the less valuable card
                if right_value < left_value:
                    return Side.RIGHT
                elif left_value < right_value:
                    return Side.LEFT

        # For market draws, pick the highest value card
        if choice_type == "market_draw":
            best_idx = 0
            best_value = float('-inf')
            for idx in choice.options:
                if idx < len(state.market):
                    value = self._card_value(state.market[idx], state, player_idx)
                    if value > best_value:
                        best_value = value
                        best_idx = idx
            return best_idx

        # For discards, discard the lowest value card
        if choice_type == "discard_hand":
            hand = state.players[player_idx].hand
            worst_idx = 0
            worst_value = float('inf')
            for idx in choice.options:
                if idx < len(hand):
                    value = self._card_value(hand[idx], state, player_idx)
                    if value < worst_value:
                        worst_value = value
                        worst_idx = idx
            return worst_idx

        # For trashing market cards, trash the lowest value
        if choice_type == "trash_market_card":
            worst_idx = 0
            worst_value = float('inf')
            for idx in choice.options:
                if idx < len(state.market):
                    value = self._card_value(state.market[idx], state, player_idx)
                    if value < worst_value:
                        worst_value = value
                        worst_idx = idx
            return worst_idx

        # For Turncoat, swap with opponent's best card
        if choice_type == "turncoat_target":
            opponent_row = state.players[1 - player_idx].row
            best_idx = 0
            best_value = float('-inf')
            for idx in choice.options:
                if idx < len(opponent_row):
                    value = self._card_value(opponent_row[idx].card, state, player_idx)
                    if value > best_value:
                        best_value = value
                        best_idx = idx
            return best_idx

        # Default: random choice
        return self.rng.choice(choice.options)
