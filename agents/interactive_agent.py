"""
Interactive agent that waits for external input via API calls.
Uses asyncio primitives for synchronization with the API layer.
"""

import asyncio
from typing import Any

from game.state import GameState, PlayAction, DrawChoice, EffectChoice
from agents.base import Agent


class InteractiveAgent(Agent):
    """
    Agent implementation that awaits external decisions.
    Used in the API mode where a human player makes decisions via HTTP requests.

    All methods are async and use asyncio.Queue for receiving input.
    """

    def __init__(self):
        # Input queues (asyncio-based)
        self._action_queue: asyncio.Queue[PlayAction] | None = None
        self._draw_queue: asyncio.Queue[DrawChoice] | None = None
        self._effect_queue: asyncio.Queue[Any] | None = None

        # State tracking
        self._waiting_for: str | None = None
        self._last_effect_choice: EffectChoice | None = None

        # Event for signaling state changes
        self._state_changed: asyncio.Event | None = None
        self._input_processed: asyncio.Event | None = None

    def _ensure_queues(self) -> None:
        """Ensure queues are created in the current event loop."""
        if self._action_queue is None:
            self._action_queue = asyncio.Queue()
            self._draw_queue = asyncio.Queue()
            self._effect_queue = asyncio.Queue()
            self._state_changed = asyncio.Event()
            self._input_processed = asyncio.Event()

    @property
    def waiting_for(self) -> str | None:
        """Get what type of input the agent is waiting for."""
        return self._waiting_for

    @property
    def last_effect_choice(self) -> EffectChoice | None:
        """Get the last effect choice that was requested."""
        return self._last_effect_choice

    def _set_waiting(self, waiting_type: str | None, effect_choice: EffectChoice | None = None) -> None:
        """Set the waiting state and signal the change."""
        self._waiting_for = waiting_type
        self._last_effect_choice = effect_choice
        if self._state_changed:
            self._state_changed.set()

    async def choose_action(self, state: GameState, player_idx: int) -> PlayAction:
        """Wait for a PlayAction to be submitted via the API."""
        self._ensure_queues()
        if self._input_processed:
            self._input_processed.clear()
        self._set_waiting('action')

        try:
            action = await asyncio.wait_for(self._action_queue.get(), timeout=300)
            self._set_waiting(None)
            if self._input_processed:
                self._input_processed.set()
            return action
        except asyncio.TimeoutError:
            self._set_waiting(None)
            raise TimeoutError("No action received within timeout period")

    async def choose_draw(self, state: GameState, player_idx: int) -> DrawChoice:
        """Wait for a DrawChoice to be submitted via the API."""
        self._ensure_queues()
        if self._input_processed:
            self._input_processed.clear()
        self._set_waiting('draw')

        try:
            choice = await asyncio.wait_for(self._draw_queue.get(), timeout=300)
            self._set_waiting(None)
            if self._input_processed:
                self._input_processed.set()
            return choice
        except asyncio.TimeoutError:
            self._set_waiting(None)
            raise TimeoutError("No draw choice received within timeout period")

    async def choose_effect_option(
        self, state: GameState, player_idx: int, choice: EffectChoice
    ) -> Any:
        """Wait for an effect choice to be submitted via the API."""
        self._ensure_queues()
        if self._input_processed:
            self._input_processed.clear()
        self._set_waiting('effect', choice)

        try:
            option = await asyncio.wait_for(self._effect_queue.get(), timeout=300)
            self._set_waiting(None)
            if self._input_processed:
                self._input_processed.set()
            return option
        except asyncio.TimeoutError:
            self._set_waiting(None)
            raise TimeoutError("No effect choice received within timeout period")

    async def submit_action(self, action: PlayAction) -> None:
        """Queue an action from the API."""
        self._ensure_queues()
        await self._action_queue.put(action)

    async def submit_draw(self, choice: DrawChoice) -> None:
        """Queue a draw choice from the API."""
        self._ensure_queues()
        await self._draw_queue.put(choice)

    async def submit_effect_choice(self, option: Any) -> None:
        """Queue an effect choice from the API."""
        self._ensure_queues()
        await self._effect_queue.put(option)

    async def submit_market_draw(self, market_index: int) -> None:
        """
        Submit a market draw with card selection as an atomic operation.
        This queues both the draw choice and the market index selection.
        """
        self._ensure_queues()
        await self._draw_queue.put(DrawChoice.MARKET)
        await self._effect_queue.put(market_index)

    def is_waiting(self) -> bool:
        """Check if the agent is currently waiting for input."""
        return self._waiting_for is not None

    def get_waiting_for(self) -> str | None:
        """Get what type of input the agent is waiting for."""
        return self._waiting_for

    async def wait_for_processing(self, timeout: float = 5.0) -> bool:
        """
        Wait for the current input to be processed by the game.

        Returns True if processing completed, False if timeout.
        """
        self._ensure_queues()
        try:
            await asyncio.wait_for(self._input_processed.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def wait_for_waiting_state(self, timeout: float = 5.0) -> bool:
        """
        Wait for the agent to enter a waiting state.

        Returns True if now waiting, False if timeout.
        """
        self._ensure_queues()
        self._state_changed.clear()
        if self._waiting_for is not None:
            return True
        try:
            await asyncio.wait_for(self._state_changed.wait(), timeout=timeout)
            return self._waiting_for is not None
        except asyncio.TimeoutError:
            return False
