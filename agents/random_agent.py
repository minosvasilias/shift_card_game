"""Random agent that makes valid random moves."""

from __future__ import annotations

import random
from typing import Any

from game.state import GameState, PlayAction, DrawChoice, EffectChoice, Side, CardType
from .base import Agent


class RandomAgent(Agent):
    """Agent that makes uniformly random valid moves."""

    def __init__(self, seed: int | None = None):
        """
        Initialize the random agent.

        Args:
            seed: Optional random seed for reproducibility
        """
        self.rng = random.Random(seed)

    async def choose_action(self, state: GameState, player_idx: int) -> PlayAction:
        """Choose a random card and side to play."""
        player = state.players[player_idx]
        hand = player.hand

        if not hand:
            # No cards to play - this shouldn't happen normally
            return PlayAction(hand_index=0, side=Side.LEFT)

        # Choose random card from hand
        hand_index = self.rng.randint(0, len(hand) - 1)
        card = hand[hand_index]

        # Choose random side
        side = self.rng.choice([Side.LEFT, Side.RIGHT])

        # Decide whether to play face-down (only for traps)
        face_down = False
        if card.card_type == CardType.TRAP:
            face_down = self.rng.choice([True, False])

        return PlayAction(
            hand_index=hand_index,
            side=side,
            face_down=face_down,
        )

    async def choose_draw(self, state: GameState, player_idx: int) -> DrawChoice:
        """Choose randomly between deck and market."""
        # Check what's available
        has_deck = bool(state.deck)
        has_market = bool(state.market) and not state.has_embargo(player_idx)

        if has_deck and has_market:
            return self.rng.choice([DrawChoice.DECK, DrawChoice.MARKET])
        elif has_deck:
            return DrawChoice.DECK
        else:
            return DrawChoice.MARKET

    async def choose_effect_option(
        self, state: GameState, player_idx: int, choice: EffectChoice
    ) -> Any:
        """Choose randomly from the available options."""
        if not choice.options:
            return None
        return self.rng.choice(choice.options)
