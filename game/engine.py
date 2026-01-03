"""Game engine for Robot Assembly Line."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from .state import (
    GameState,
    PlayerState,
    CardInPlay,
    PlayAction,
    DrawChoice,
    Side,
    Event,
    EventType,
    CardType,
    ActiveEffect,
)
from .cards import get_all_cards

if TYPE_CHECKING:
    from agents.base import Agent


class GameEngine:
    """Manages game state and turn execution."""

    def __init__(
        self,
        agents: tuple[Agent, Agent],
        card_pool: list | None = None,
        seed: int | None = None,
        max_turns: int = 10,
    ):
        """
        Initialize a new game.

        Args:
            agents: Tuple of two agents (player 0 and player 1)
            card_pool: Optional list of cards to use (defaults to all cards)
            seed: Random seed for reproducibility
            max_turns: Number of turns before game ends (default 10)
        """
        self.agents = agents
        self.max_turns = max_turns
        self.rng = random.Random(seed)

        # Initialize game state
        cards = card_pool if card_pool is not None else get_all_cards()
        deck = list(cards)
        self.rng.shuffle(deck)

        self.state = GameState(
            players=[PlayerState(), PlayerState()],
            deck=deck,
            market=[],
            turn_counter=1,
            current_player=0,
        )

        # Setup: deal 2 cards to each player
        for player in self.state.players:
            for _ in range(2):
                if self.state.deck:
                    player.hand.append(self.state.deck.pop())

        # Fill market to 3 cards
        self._refill_market()

    def _refill_market(self) -> None:
        """Refill market to 3 cards from deck."""
        while len(self.state.market) < 3 and self.state.deck:
            self.state.market.append(self.state.deck.pop())

    def _get_current_agent(self) -> Agent:
        """Get the agent for the current player."""
        return self.agents[self.state.current_player]

    def _get_opponent_agent(self) -> Agent:
        """Get the agent for the opponent."""
        return self.agents[1 - self.state.current_player]

    def _check_traps(self, event: Event) -> None:
        """Check and trigger any traps for an event."""
        # Check opponent's face-down cards for trap triggers
        opponent_idx = 1 - event.player_idx
        opponent_row = self.state.players[opponent_idx].row

        for card in list(opponent_row):  # Copy list since we may modify it
            if not card.face_up and card.card.trigger_check:
                if card.card.trigger_check(event, self.state, card, opponent_idx):
                    # Trap triggers!
                    card.face_up = True

                    # Execute trap effect
                    agent = self.agents[opponent_idx]
                    points = card.card.effect(self.state, card, opponent_idx, agent, event)
                    self.state.players[opponent_idx].score += points
                    # Record for analytics
                    self.state.record_card_score(card.name, points)

                    # Handle special trap effects
                    if card.metadata.get("cancel_score"):
                        # Tripwire and Tax Collector: cancel opponent's score
                        cancel_amount = card.metadata.pop("cancel_score")
                        self.state.players[event.player_idx].score -= cancel_amount

                    if card.metadata.get("ambush_steal_card"):
                        # Ambush: steal the card to your hand
                        card_name = card.metadata.pop("ambush_steal_card")
                        # Find and remove the card from opponent's row
                        attacker_idx = event.player_idx
                        for i, opp_card in enumerate(self.state.players[attacker_idx].row):
                            if opp_card.card.name == card_name:
                                stolen_card = self.state.players[attacker_idx].row.pop(i)
                                self.state.players[opponent_idx].hand.append(stolen_card.card)
                                # Enforce hand limit
                                from .effects import enforce_hand_limit
                                enforce_hand_limit(self.state, opponent_idx, agent)
                                break

                    if card.metadata.get("nullify_card"):
                        # Mirror Match: nullify the opponent's card
                        card_name = card.metadata.pop("nullify_card")
                        # Find and remove the card from opponent's row, send to market
                        attacker_idx = event.player_idx
                        for i, opp_card in enumerate(self.state.players[attacker_idx].row):
                            if opp_card.card.name == card_name:
                                nullified_card = self.state.players[attacker_idx].row.pop(i)
                                self.state.market.append(nullified_card.card)
                                break

    def _play_card(self, action: PlayAction) -> CardInPlay | None:
        """
        Play a card from hand to the row.

        Returns the card that was pushed out (if any).
        """
        player = self.state.current
        player_idx = self.state.current_player

        if action.hand_index >= len(player.hand):
            return None

        card = player.hand.pop(action.hand_index)
        card_in_play = CardInPlay(
            card=card,
            face_up=not action.face_down,
        )

        # Store trap side for Ambush trap
        if action.face_down and card.card_type == CardType.TRAP:
            card_in_play.metadata["trap_side"] = action.side

        # Check if card is blocked by boomerang cooldown
        for effect in self.state.active_effects:
            if (effect.effect_type == "boomerang_cooldown" and
                effect.player_idx == player_idx and
                effect.data.get("card_name") == card.name):
                # Can't play this card - put it back
                player.hand.append(card)
                return None

        # Check if side is blocked by Roadblock
        for effect in self.state.active_effects:
            if (effect.effect_type == "roadblock" and
                effect.player_idx == player_idx and
                effect.data.get("blocked_side") == action.side):
                # Can't play to this side - put card back
                player.hand.append(card)
                return None

        # Emit card played event (for Snare and Ambush traps)
        event = Event(
            event_type=EventType.CARD_PLAYED,
            player_idx=player_idx,
            card_name=card.name,
            icon=card.icon,
            data={"side": action.side},
        )
        self.state.turn_events.append(event)
        self._check_traps(event)

        # Check if Snare was triggered
        opponent_idx = 1 - player_idx
        for opp_card in self.state.players[opponent_idx].row:
            if opp_card.metadata.get("snare_card") == card.name:
                # Card goes to market instead
                self.state.market.append(card)
                opp_card.metadata.pop("snare_card")
                return None

        # Add card to row at the specified edge
        pushed_card = None

        if action.side == Side.LEFT:
            player.row.insert(0, card_in_play)
            # If row exceeds 3, push from right
            if len(player.row) > 3:
                pushed_card = player.row.pop()
                pushed_card.metadata["exit_side"] = Side.RIGHT
        else:
            player.row.append(card_in_play)
            # If row exceeds 3, push from left
            if len(player.row) > 3:
                pushed_card = player.row.pop(0)
                pushed_card.metadata["exit_side"] = Side.LEFT

        # Check for center scoring
        self._check_center_trigger(player_idx)

        return pushed_card

    def _check_center_trigger(self, player_idx: int) -> None:
        """Check if center card should trigger its effect."""
        player = self.state.players[player_idx]

        if len(player.row) != 3:
            return

        center_card = player.row[1]

        # Only face-up, center-type cards trigger
        if not center_card.face_up or center_card.card.card_type != CardType.CENTER:
            return

        # Execute center effect
        agent = self.agents[player_idx]
        points = center_card.card.effect(self.state, center_card, player_idx, agent)

        # Store for Copycat
        center_card.metadata["last_center_score"] = points

        # Apply points
        player.score += points

        # Record for analytics
        self.state.record_card_score(center_card.name, points)

        # Emit scoring event (for traps)
        if points > 0:
            event = Event(
                event_type=EventType.CARD_SCORED,
                player_idx=player_idx,
                card_name=center_card.name,
                points=points,
            )
            self.state.turn_events.append(event)
            self._check_traps(event)

        # Handle Kickback's push effect
        if "kickback_pushed_card" in center_card.metadata:
            pushed = center_card.metadata.pop("kickback_pushed_card")
            if pushed in player.row:
                player.row.remove(pushed)
                # Determine which side was pushed
                if player.row.index(center_card) == 0:
                    # Center card moved to left, so right edge was pushed
                    pushed.metadata["exit_side"] = Side.RIGHT
                else:
                    # Center card moved to right, so left edge was pushed
                    pushed.metadata["exit_side"] = Side.LEFT
                self._handle_pushed_card(pushed, player_idx)

        # Handle Compressor's double push effect
        if "compressor_pushed_cards" in center_card.metadata:
            pushed_cards = center_card.metadata.pop("compressor_pushed_cards")
            for i, pushed in enumerate(pushed_cards):
                if pushed in player.row:
                    player.row.remove(pushed)
                    # First card is left edge, second is right edge
                    pushed.metadata["exit_side"] = Side.LEFT if i == 0 else Side.RIGHT
                    self._handle_pushed_card(pushed, player_idx)

        # Handle Sniper's targeted push effect
        if "sniper_target" in center_card.metadata:
            sniped_card = center_card.metadata.pop("sniper_target")
            target_idx = center_card.metadata.pop("sniper_target_idx")
            opponent_idx = center_card.metadata.pop("sniper_opponent_idx")
            opponent_row = self.state.players[opponent_idx].row

            if sniped_card in opponent_row:
                opponent_row.remove(sniped_card)
                # Determine which side based on original position
                if target_idx == 0:
                    sniped_card.metadata["exit_side"] = Side.LEFT
                elif target_idx == len(opponent_row):  # Was rightmost before removal
                    sniped_card.metadata["exit_side"] = Side.RIGHT
                else:
                    # Middle card - default to left
                    sniped_card.metadata["exit_side"] = Side.LEFT
                self._handle_pushed_card(sniped_card, opponent_idx)

        # Check for pending hand limit enforcement (e.g., from Hot Potato)
        self._enforce_pending_hand_limits()

    def _enforce_pending_hand_limits(self) -> None:
        """Enforce hand limits for any players marked as needing it."""
        from .state import EffectChoice

        for check_player_idx, protected_card_name in list(self.state.pending_hand_limit_checks.items()):
            player = self.state.players[check_player_idx]
            agent = self.agents[check_player_idx]

            while len(player.hand) > 2:
                # Build options excluding the protected card (the one just received)
                options = [
                    i for i, card in enumerate(player.hand)
                    if card.name != protected_card_name
                ]

                if not options:
                    # Edge case: all cards are protected (shouldn't happen normally)
                    options = list(range(len(player.hand)))

                choice = EffectChoice(
                    choice_type="discard_hand",
                    options=options,
                    description=f"Choose which card to discard (cannot discard {protected_card_name})",
                )
                discard_idx = agent.choose_effect_option(self.state, check_player_idx, choice)
                player.hand.pop(discard_idx)

            del self.state.pending_hand_limit_checks[check_player_idx]

    def _handle_pushed_card(self, pushed_card: CardInPlay, player_idx: int) -> None:
        """Handle a card that was pushed out of the row."""
        # Trigger exit effect if applicable
        if pushed_card.face_up and pushed_card.card.card_type == CardType.EXIT:
            agent = self.agents[player_idx]
            points = pushed_card.card.effect(self.state, pushed_card, player_idx, agent)
            self.state.players[player_idx].score += points
            # Record for analytics
            self.state.record_card_score(pushed_card.name, points)

            # Handle Sabotage effect
            if pushed_card.metadata.get("pending_sabotage"):
                pushed_card.metadata.pop("pending_sabotage")
                opponent_idx = 1 - player_idx
                opponent_row = self.state.players[opponent_idx].row
                opponent_agent = self.agents[opponent_idx]

                if opponent_row:
                    from .state import EffectChoice
                    choice = EffectChoice(
                        choice_type="sabotage_edge",
                        options=[Side.LEFT, Side.RIGHT] if len(opponent_row) > 1 else [Side.LEFT],
                        description="Choose which edge card to trash (Sabotage)"
                    )
                    edge_choice = opponent_agent.choose_effect_option(self.state, opponent_idx, choice)

                    # Remove and trash the chosen edge card
                    if edge_choice == Side.LEFT:
                        opponent_row.pop(0)
                    else:
                        opponent_row.pop(-1)

        # Handle Phoenix - goes to top of deck instead of market
        if pushed_card.metadata.get("phoenix_to_deck"):
            self.state.deck.append(pushed_card.card)
        # Add to market (unless special handling)
        elif not pushed_card.metadata.get("skip_market"):
            self.state.market.append(pushed_card.card)

        # Handle market overflow
        if len(self.state.market) > 3:
            # Current player chooses which card to trash
            agent = self.agents[player_idx]
            from .state import EffectChoice
            choice = EffectChoice(
                choice_type="trash_market_card",
                options=list(range(len(self.state.market))),
                description="Choose which market card to trash",
            )
            trash_idx = agent.choose_effect_option(self.state, player_idx, choice)
            self.state.market.pop(trash_idx)

    def _handle_draw(self, player_idx: int) -> None:
        """Handle the draw phase."""
        player = self.state.players[player_idx]
        agent = self.agents[player_idx]

        # Check for embargo
        has_embargo = self.state.has_embargo(player_idx)

        # Get valid draw options
        can_draw_deck = bool(self.state.deck)
        can_draw_market = bool(self.state.market) and not has_embargo

        if not can_draw_deck and not can_draw_market:
            return

        # Get agent's choice
        draw_choice = agent.choose_draw(self.state, player_idx)

        # Validate choice
        if draw_choice == DrawChoice.DECK and not can_draw_deck:
            draw_choice = DrawChoice.MARKET
        elif draw_choice == DrawChoice.MARKET and not can_draw_market:
            draw_choice = DrawChoice.DECK

        if draw_choice == DrawChoice.DECK:
            if self.state.deck:
                drawn = self.state.deck.pop()
                player.hand.append(drawn)
        else:
            if self.state.market:
                # Agent chooses which market card
                from .state import EffectChoice
                choice = EffectChoice(
                    choice_type="market_draw",
                    options=list(range(len(self.state.market))),
                    description="Choose which market card to take",
                )
                market_idx = agent.choose_effect_option(self.state, player_idx, choice)

                # Check for False Flag trap
                opponent_idx = 1 - player_idx
                redirected = False
                for opp_card in self.state.players[opponent_idx].row:
                    if opp_card.metadata.get("redirect_card"):
                        # Card goes to opponent instead
                        drawn = self.state.market.pop(market_idx)
                        self.state.players[opponent_idx].hand.append(drawn)
                        opp_card.metadata.pop("redirect_card")
                        redirected = True
                        break

                if not redirected:
                    drawn = self.state.market.pop(market_idx)
                    player.hand.append(drawn)

                    # Emit event
                    event = Event(
                        event_type=EventType.CARD_DRAWN_MARKET,
                        player_idx=player_idx,
                        card_name=drawn.name,
                    )
                    self.state.turn_events.append(event)
                    self._check_traps(event)

        # Handle hand limit
        while len(player.hand) > 2:
            from .state import EffectChoice
            choice = EffectChoice(
                choice_type="discard_hand",
                options=list(range(len(player.hand))),
                description="Choose which card to discard (hand limit is 2)",
            )
            discard_idx = agent.choose_effect_option(self.state, player_idx, choice)
            player.hand.pop(discard_idx)

    def _cleanup_expired_effects(self) -> None:
        """Remove expired active effects."""
        self.state.active_effects = [
            e for e in self.state.active_effects
            if e.expires_turn is None or e.expires_turn > self.state.turn_counter
        ]

    def _handle_pending_effects(self, player_idx: int) -> None:
        """Handle any pending effects from card plays."""
        player = self.state.players[player_idx]
        opponent_idx = 1 - player_idx
        opponent = self.state.players[opponent_idx]

        for card in list(player.row):
            # Tug-of-War
            if card.metadata.get("pending_tug_of_war") and len(opponent.row) == 3:
                from .state import EffectChoice, Side
                agent = self.agents[opponent_idx]
                choice = EffectChoice(
                    choice_type="tug_of_war_edge",
                    options=[Side.LEFT, Side.RIGHT],
                    description="Choose which edge card to push out",
                )
                edge = agent.choose_effect_option(self.state, opponent_idx, choice)
                if edge == Side.LEFT:
                    pushed = opponent.row.pop(0)
                else:
                    pushed = opponent.row.pop()
                self._handle_pushed_card(pushed, opponent_idx)
                card.metadata.pop("pending_tug_of_war")

            # Spite Module
            if card.metadata.get("pending_spite_module") and opponent.row:
                from .state import EffectChoice, Side
                agent = self.agents[opponent_idx]
                options = [Side.LEFT]
                if len(opponent.row) > 1:
                    options.append(Side.RIGHT)
                choice = EffectChoice(
                    choice_type="spite_module_edge",
                    options=options,
                    description="Choose which edge card to push out",
                )
                edge = agent.choose_effect_option(self.state, opponent_idx, choice)
                if edge == Side.LEFT:
                    pushed = opponent.row.pop(0)
                else:
                    pushed = opponent.row.pop()
                # No center score for this push
                self.state.market.append(pushed.card)
                card.metadata.pop("pending_spite_module")

    def play_turn(self) -> bool:
        """
        Execute one turn for the current player.

        Returns True if game continues, False if game is over.
        """
        if self.state.game_over:
            return False

        player_idx = self.state.current_player
        player = self.state.current
        agent = self._get_current_agent()

        # Clear turn events
        self.state.turn_events = []

        # 1. Play a card
        if player.hand:
            action = agent.choose_action(self.state, player_idx)
            pushed_card = self._play_card(action)

            # 2. Handle pushed card
            if pushed_card:
                self._handle_pushed_card(pushed_card, player_idx)

        # 3. Handle pending effects
        self._handle_pending_effects(player_idx)

        # 4. Draw a card
        self._handle_draw(player_idx)

        # 5. Refill market
        self._refill_market()

        # 6. Cleanup expired effects
        self._cleanup_expired_effects()

        # 7. Check game end
        if self.state.turn_counter >= self.max_turns * 2:  # Each player takes max_turns
            self._end_game()
            return False

        # Advance turn
        self.state.current_player = 1 - self.state.current_player
        if self.state.current_player == 0:
            self.state.turn_counter += 1

        return True

    def _end_game(self) -> None:
        """Handle end of game scoring and cleanup."""
        # Handle Patience Circuit delayed scoring
        for player_idx, player in enumerate(self.state.players):
            for card in player.row:
                if "patience_turn" in card.metadata:
                    turns_elapsed = self.state.turn_counter - card.metadata["patience_turn"]
                    player.score += turns_elapsed
                    # Record for analytics
                    self.state.record_card_score(card.name, turns_elapsed)

        self.state.game_over = True

    def run_game(self) -> GameState:
        """Run the entire game and return the final state."""
        while self.play_turn():
            pass
        return self.state

    def get_winner(self) -> int | None:
        """
        Get the winner of the game.

        Returns 0 or 1 for the winning player, or None for a tie.
        """
        if not self.state.game_over:
            return None

        p0_score = self.state.players[0].score
        p1_score = self.state.players[1].score

        if p0_score > p1_score:
            return 0
        elif p1_score > p0_score:
            return 1
        else:
            # Tiebreaker: more cards in row
            p0_cards = len(self.state.players[0].row)
            p1_cards = len(self.state.players[1].row)
            if p0_cards > p1_cards:
                return 0
            elif p1_cards > p0_cards:
                return 1
            else:
                return None  # True tie
