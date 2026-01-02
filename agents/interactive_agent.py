"""
Interactive agent that waits for external input via API calls.
"""

from typing import Any
from queue import Queue, Empty
from game.state import GameState, PlayAction, DrawChoice, EffectChoice
from agents.base import Agent


class InteractiveAgent(Agent):
    """
    Agent implementation that blocks and waits for external decisions.
    Used in the API mode where a human player makes decisions via HTTP requests.
    """

    def __init__(self):
        self.action_queue: Queue[PlayAction] = Queue()
        self.draw_queue: Queue[DrawChoice] = Queue()
        self.effect_queue: Queue[Any] = Queue()
        self.waiting_for: str | None = None  # 'action', 'draw', or 'effect'
        self.last_effect_choice: EffectChoice | None = None

    def choose_action(self, state: GameState, player_idx: int) -> PlayAction:
        """Wait for a PlayAction to be submitted via the API."""
        self.waiting_for = 'action'
        try:
            action = self.action_queue.get(timeout=300)  # 5 min timeout
            self.waiting_for = None
            return action
        except Empty:
            raise TimeoutError("No action received within timeout period")

    def choose_draw(self, state: GameState, player_idx: int) -> DrawChoice:
        """Wait for a DrawChoice to be submitted via the API."""
        self.waiting_for = 'draw'
        try:
            choice = self.draw_queue.get(timeout=300)  # 5 min timeout
            self.waiting_for = None
            return choice
        except Empty:
            raise TimeoutError("No draw choice received within timeout period")

    def choose_effect_option(
        self, state: GameState, player_idx: int, choice: EffectChoice
    ) -> Any:
        """Wait for an effect choice to be submitted via the API."""
        self.waiting_for = 'effect'
        self.last_effect_choice = choice
        try:
            option = self.effect_queue.get(timeout=300)  # 5 min timeout
            self.waiting_for = None
            self.last_effect_choice = None
            return option
        except Empty:
            raise TimeoutError("No effect choice received within timeout period")

    def submit_action(self, action: PlayAction) -> None:
        """Queue an action from the API."""
        self.action_queue.put(action)

    def submit_draw(self, choice: DrawChoice) -> None:
        """Queue a draw choice from the API."""
        self.draw_queue.put(choice)

    def submit_effect_choice(self, option: Any) -> None:
        """Queue an effect choice from the API."""
        self.effect_queue.put(option)

    def is_waiting(self) -> bool:
        """Check if the agent is currently waiting for input."""
        return self.waiting_for is not None

    def get_waiting_for(self) -> str | None:
        """Get what type of input the agent is waiting for."""
        return self.waiting_for
