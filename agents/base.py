"""Base Agent interface for Robot Assembly Line."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from game.state import GameState, PlayAction, DrawChoice, EffectChoice


class Agent(ABC):
    """Abstract base class for game-playing agents.

    All agent methods are async to support both AI agents (which complete
    immediately) and interactive agents (which await user input).
    """

    @abstractmethod
    async def choose_action(self, state: GameState, player_idx: int) -> PlayAction:
        """
        Choose which card to play and where.

        Args:
            state: Current game state
            player_idx: Index of the player (0 or 1)

        Returns:
            PlayAction specifying which card to play and where
        """
        pass

    @abstractmethod
    async def choose_draw(self, state: GameState, player_idx: int) -> DrawChoice:
        """
        Choose where to draw a card from.

        Args:
            state: Current game state
            player_idx: Index of the player (0 or 1)

        Returns:
            DrawChoice (DECK or MARKET)
        """
        pass

    @abstractmethod
    async def choose_effect_option(
        self, state: GameState, player_idx: int, choice: EffectChoice
    ) -> Any:
        """
        Make a choice required by a card effect.

        This is called when a card effect requires the player to make a decision,
        such as choosing which card to target, which direction to move, etc.

        Args:
            state: Current game state
            player_idx: Index of the player making the choice
            choice: EffectChoice describing the decision to be made

        Returns:
            The selected option from choice.options
        """
        pass

    async def on_game_start(self, state: GameState, player_idx: int) -> None:
        """
        Called when a game starts. Override for any initialization.

        Args:
            state: Initial game state
            player_idx: Index of this agent (0 or 1)
        """
        pass

    async def on_game_end(self, state: GameState, player_idx: int) -> None:
        """
        Called when a game ends. Override for any cleanup or learning.

        Args:
            state: Final game state
            player_idx: Index of this agent (0 or 1)
        """
        pass
