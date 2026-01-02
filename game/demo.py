"""Demo game runner with step-by-step visualization."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Callable

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
from .display import (
    format_game_state,
    format_action,
    format_push,
    format_center_score,
    format_draw,
    format_game_end,
)

if TYPE_CHECKING:
    from agents.base import Agent

import random


class DemoEngine:
    """Game engine with step-by-step logging for demos."""

    def __init__(
        self,
        agents: tuple[Agent, Agent],
        card_pool: list | None = None,
        seed: int | None = None,
        max_turns: int = 10,
        delay: float = 0.5,
        log_fn: Callable[[str], None] | None = None,
    ):
        """
        Initialize a demo game.

        Args:
            agents: Tuple of two agents
            card_pool: Optional list of cards to use
            seed: Random seed for reproducibility
            max_turns: Number of turns before game ends
            delay: Delay between actions (seconds)
            log_fn: Function to call with log messages (default: print)
        """
        self.agents = agents
        self.max_turns = max_turns
        self.delay = delay
        self.log = log_fn or print
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

    def _pause(self):
        """Pause for effect."""
        if self.delay > 0:
            time.sleep(self.delay)

    def _refill_market(self) -> None:
        """Refill market to 3 cards from deck."""
        while len(self.state.market) < 3 and self.state.deck:
            self.state.market.append(self.state.deck.pop())

    def _get_current_agent(self) -> Agent:
        return self.agents[self.state.current_player]

    def _check_traps(self, event: Event) -> None:
        """Check and trigger any traps for an event."""
        opponent_idx = 1 - event.player_idx
        opponent_row = self.state.players[opponent_idx].row

        for card in list(opponent_row):
            if not card.face_up and card.card.trigger_check:
                if card.card.trigger_check(event, self.state, card, opponent_idx):
                    card.face_up = True
                    self.log(f"  ⚠ TRAP TRIGGERED: [{card.card.name}]!")

                    agent = self.agents[opponent_idx]
                    points = card.card.effect(self.state, card, opponent_idx, agent, event)
                    self.state.players[opponent_idx].score += points

                    if points > 0:
                        self.log(f"    P{opponent_idx} scores {points} from trap")

                    if card.metadata.get("cancel_score"):
                        cancel_amount = card.metadata["cancel_score"]
                        self.state.players[event.player_idx].score -= cancel_amount
                        self.log(f"    P{event.player_idx}'s score cancelled (-{cancel_amount})")

    def _play_card(self, action: PlayAction) -> CardInPlay | None:
        """Play a card from hand to the row."""
        player = self.state.current
        player_idx = self.state.current_player

        if action.hand_index >= len(player.hand):
            return None

        card = player.hand.pop(action.hand_index)
        card_in_play = CardInPlay(
            card=card,
            face_up=not action.face_down,
        )

        # Check boomerang cooldown
        for effect in self.state.active_effects:
            if (effect.effect_type == "boomerang_cooldown" and
                effect.player_idx == player_idx and
                effect.data.get("card_name") == card.name):
                player.hand.append(card)
                self.log(f"  ✗ Cannot play [{card.name}] - Boomerang cooldown!")
                return None

        # Log the action
        self.log(format_action(player_idx, card.name, action.side, action.face_down))
        self._pause()

        # Emit card played event
        event = Event(
            event_type=EventType.CARD_PLAYED,
            player_idx=player_idx,
            card_name=card.name,
            icon=card.icon,
        )
        self.state.turn_events.append(event)
        self._check_traps(event)

        # Check Snare
        opponent_idx = 1 - player_idx
        for opp_card in self.state.players[opponent_idx].row:
            if opp_card.metadata.get("snare_card") == card.name:
                self.state.market.append(card)
                opp_card.metadata.pop("snare_card")
                self.log(f"  ⚠ SNARED! [{card.name}] goes to market instead")
                return None

        # Add card to row
        pushed_card = None

        if action.side == Side.LEFT:
            player.row.insert(0, card_in_play)
            if len(player.row) > 3:
                pushed_card = player.row.pop()
        else:
            player.row.append(card_in_play)
            if len(player.row) > 3:
                pushed_card = player.row.pop(0)

        # Check center scoring
        self._check_center_trigger(player_idx)

        return pushed_card

    def _check_center_trigger(self, player_idx: int) -> None:
        """Check if center card should trigger."""
        player = self.state.players[player_idx]

        if len(player.row) != 3:
            return

        center_card = player.row[1]

        if not center_card.face_up or center_card.card.card_type != CardType.CENTER:
            return

        agent = self.agents[player_idx]
        points = center_card.card.effect(self.state, center_card, player_idx, agent)

        center_card.metadata["last_center_score"] = points
        player.score += points

        if points != 0:
            self.log(format_center_score(center_card.name, points))
            self._pause()

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
                self.log(f"  ⚡ Kickback pushes [{pushed.name}] out!")
                self._handle_pushed_card(pushed, player_idx)

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
                discarded = player.hand.pop(discard_idx)
                self.log(f"  ✗ Hand limit - P{check_player_idx} discards [{discarded.name}]")

            del self.state.pending_hand_limit_checks[check_player_idx]

    def _handle_pushed_card(self, pushed_card: CardInPlay, player_idx: int) -> None:
        """Handle a pushed out card."""
        points = 0

        if pushed_card.face_up and pushed_card.card.card_type == CardType.EXIT:
            agent = self.agents[player_idx]
            points = pushed_card.card.effect(self.state, pushed_card, player_idx, agent)
            self.state.players[player_idx].score += points

        self.log(format_push(pushed_card.name, points))
        self._pause()

        if not pushed_card.metadata.get("skip_market"):
            self.state.market.append(pushed_card.card)

        # Handle market overflow
        if len(self.state.market) > 3:
            agent = self.agents[player_idx]
            from .state import EffectChoice
            choice = EffectChoice(
                choice_type="trash_market_card",
                options=list(range(len(self.state.market))),
                description="Choose which market card to trash",
            )
            trash_idx = agent.choose_effect_option(self.state, player_idx, choice)
            trashed = self.state.market.pop(trash_idx)
            self.log(f"  ✗ Market full - [{trashed.name}] trashed")

    def _handle_draw(self, player_idx: int) -> None:
        """Handle draw phase."""
        player = self.state.players[player_idx]
        agent = self.agents[player_idx]

        has_embargo = self.state.has_embargo(player_idx)
        can_draw_deck = bool(self.state.deck)
        can_draw_market = bool(self.state.market) and not has_embargo

        if not can_draw_deck and not can_draw_market:
            self.log(f"  ↓ P{player_idx} cannot draw (no cards available)")
            return

        if has_embargo:
            self.log(f"  ⚠ Market locked by Embargo")

        draw_choice = agent.choose_draw(self.state, player_idx)

        if draw_choice == DrawChoice.DECK and not can_draw_deck:
            draw_choice = DrawChoice.MARKET
        elif draw_choice == DrawChoice.MARKET and not can_draw_market:
            draw_choice = DrawChoice.DECK

        if draw_choice == DrawChoice.DECK:
            if self.state.deck:
                drawn = self.state.deck.pop()
                player.hand.append(drawn)
                self.log(format_draw(player_idx, "DECK", drawn.name))
        else:
            if self.state.market:
                from .state import EffectChoice
                choice = EffectChoice(
                    choice_type="market_draw",
                    options=list(range(len(self.state.market))),
                    description="Choose market card",
                )
                market_idx = agent.choose_effect_option(self.state, player_idx, choice)

                # Check False Flag
                opponent_idx = 1 - player_idx
                redirected = False
                for opp_card in self.state.players[opponent_idx].row:
                    if opp_card.metadata.get("redirect_card"):
                        drawn = self.state.market.pop(market_idx)
                        self.state.players[opponent_idx].hand.append(drawn)
                        opp_card.metadata.pop("redirect_card")
                        self.log(f"  ⚠ FALSE FLAG! [{drawn.name}] goes to P{opponent_idx} instead")
                        redirected = True
                        break

                if not redirected:
                    drawn = self.state.market.pop(market_idx)
                    player.hand.append(drawn)
                    self.log(format_draw(player_idx, "MARKET", drawn.name))

                    event = Event(
                        event_type=EventType.CARD_DRAWN_MARKET,
                        player_idx=player_idx,
                        card_name=drawn.name,
                    )
                    self.state.turn_events.append(event)
                    self._check_traps(event)

        self._pause()

        # Handle hand limit
        while len(player.hand) > 2:
            from .state import EffectChoice
            choice = EffectChoice(
                choice_type="discard_hand",
                options=list(range(len(player.hand))),
                description="Discard to hand limit",
            )
            discard_idx = agent.choose_effect_option(self.state, player_idx, choice)
            discarded = player.hand.pop(discard_idx)
            self.log(f"  ✗ Hand limit - P{player_idx} discards [{discarded.name}]")

    def _cleanup_expired_effects(self) -> None:
        self.state.active_effects = [
            e for e in self.state.active_effects
            if e.expires_turn is None or e.expires_turn > self.state.turn_counter
        ]

    def _handle_pending_effects(self, player_idx: int) -> None:
        """Handle pending effects."""
        player = self.state.players[player_idx]
        opponent_idx = 1 - player_idx
        opponent = self.state.players[opponent_idx]

        for card in list(player.row):
            if card.metadata.get("pending_tug_of_war") and len(opponent.row) == 3:
                from .state import EffectChoice, Side
                agent = self.agents[opponent_idx]
                choice = EffectChoice(
                    choice_type="tug_of_war_edge",
                    options=[Side.LEFT, Side.RIGHT],
                    description="Choose edge to push",
                )
                edge = agent.choose_effect_option(self.state, opponent_idx, choice)
                edge_name = "LEFT" if edge == Side.LEFT else "RIGHT"
                if edge == Side.LEFT:
                    pushed = opponent.row.pop(0)
                else:
                    pushed = opponent.row.pop()
                self.log(f"  ⚔ Tug-of-War forces P{opponent_idx} to push {edge_name}")
                self._handle_pushed_card(pushed, opponent_idx)
                card.metadata.pop("pending_tug_of_war")

            if card.metadata.get("pending_spite_module") and opponent.row:
                from .state import EffectChoice, Side
                agent = self.agents[opponent_idx]
                options = [Side.LEFT]
                if len(opponent.row) > 1:
                    options.append(Side.RIGHT)
                choice = EffectChoice(
                    choice_type="spite_module_edge",
                    options=options,
                    description="Choose edge to push",
                )
                edge = agent.choose_effect_option(self.state, opponent_idx, choice)
                if edge == Side.LEFT:
                    pushed = opponent.row.pop(0)
                else:
                    pushed = opponent.row.pop()
                self.log(f"  ⚔ Spite Module forces P{opponent_idx} to push")
                self.state.market.append(pushed.card)
                card.metadata.pop("pending_spite_module")

    def play_turn(self) -> bool:
        """Execute one turn with logging."""
        if self.state.game_over:
            return False

        player_idx = self.state.current_player
        player = self.state.current
        agent = self._get_current_agent()

        # Show state at start of turn
        self.log("")
        self.log(format_game_state(self.state, show_hands=True))
        self.log("")
        self.log(f"--- P{player_idx}'s Turn ---")
        self._pause()

        self.state.turn_events = []

        # Play card
        if player.hand:
            action = agent.choose_action(self.state, player_idx)
            pushed_card = self._play_card(action)

            if pushed_card:
                self._handle_pushed_card(pushed_card, player_idx)

        # Pending effects
        self._handle_pending_effects(player_idx)

        # Draw
        self._handle_draw(player_idx)

        # Refill market
        self._refill_market()

        # Cleanup
        self._cleanup_expired_effects()

        # Check game end
        if self.state.turn_counter >= self.max_turns * 2:
            self._end_game()
            return False

        # Advance turn
        self.state.current_player = 1 - self.state.current_player
        if self.state.current_player == 0:
            self.state.turn_counter += 1

        return True

    def _end_game(self) -> None:
        """Handle end of game."""
        for player_idx, player in enumerate(self.state.players):
            for card in player.row:
                if "patience_turn" in card.metadata:
                    turns_elapsed = self.state.turn_counter - card.metadata["patience_turn"]
                    player.score += turns_elapsed
                    self.log(f"  ⏰ Patience Circuit scores {turns_elapsed} for P{player_idx}")

        self.state.game_over = True

    def run_demo(self) -> GameState:
        """Run the entire game with visualization."""
        self.log("")
        self.log("╔════════════════════════════════════════════════════════════╗")
        self.log("║          ROBOT ASSEMBLY LINE - DEMO GAME                   ║")
        self.log("╚════════════════════════════════════════════════════════════╝")
        self._pause()

        while self.play_turn():
            pass

        # Show final state
        self.log("")
        self.log(format_game_state(self.state, show_hands=False))

        # Determine winner
        p0_score = self.state.players[0].score
        p1_score = self.state.players[1].score

        if p0_score > p1_score:
            winner = 0
        elif p1_score > p0_score:
            winner = 1
        else:
            p0_cards = len(self.state.players[0].row)
            p1_cards = len(self.state.players[1].row)
            if p0_cards > p1_cards:
                winner = 0
            elif p1_cards > p0_cards:
                winner = 1
            else:
                winner = None

        self.log(format_game_end(self.state, winner))

        return self.state

    def get_winner(self) -> int | None:
        """Get the winner."""
        if not self.state.game_over:
            return None

        p0_score = self.state.players[0].score
        p1_score = self.state.players[1].score

        if p0_score > p1_score:
            return 0
        elif p1_score > p0_score:
            return 1
        else:
            p0_cards = len(self.state.players[0].row)
            p1_cards = len(self.state.players[1].row)
            if p0_cards > p1_cards:
                return 0
            elif p1_cards > p0_cards:
                return 1
            return None
