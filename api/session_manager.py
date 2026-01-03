"""
Game session manager for tracking and running interactive games.
Uses pure asyncio for running the async game engine.
"""

import asyncio
from typing import Any, Dict, Literal

from game.engine import GameEngine
from game.state import GameState, PlayAction, DrawChoice, EffectChoice
from agents.interactive_agent import InteractiveAgent
from agents.random_agent import RandomAgent
from agents.greedy_agent import GreedyAgent
from agents.lookahead_agent import LookaheadAgent


class GameSession:
    """
    Manages a single game session with an interactive player.
    Runs the game as an async task.
    """

    def __init__(
        self,
        game_id: str,
        opponent: Literal['random', 'greedy', 'lookahead'],
        seed: int | None = None,
        max_turns: int = 10,
    ):
        self.game_id = game_id
        self.interactive_agent = InteractiveAgent()

        # Create opponent agent
        if opponent == 'random':
            self.opponent_agent = RandomAgent()
        elif opponent == 'greedy':
            self.opponent_agent = GreedyAgent()
        elif opponent == 'lookahead':
            self.opponent_agent = LookaheadAgent(depth=2)
        else:
            raise ValueError(f"Unknown opponent type: {opponent}")

        # Interactive player is always player 0
        self.engine = GameEngine(
            agents=(self.interactive_agent, self.opponent_agent),
            seed=seed,
            max_turns=max_turns,
        )

        self._game_task: asyncio.Task | None = None
        self._is_running = False
        self._error: Exception | None = None

    async def start(self) -> None:
        """Start the game as a background async task."""
        self._is_running = True
        self._game_task = asyncio.create_task(self._run_game())

    async def _run_game(self) -> None:
        """Run the game loop."""
        try:
            while self._is_running:
                if self.engine.state.game_over:
                    break

                # play_turn() will await when waiting for interactive player input
                continue_game = await self.engine.play_turn()

                if not continue_game:
                    break
        except Exception as e:
            self._error = e
        finally:
            self._is_running = False

    def get_state(self) -> GameState:
        """Get the current game state."""
        return self.engine.state.copy()

    def get_winner(self) -> int | None:
        """Get the winner of the game."""
        return self.engine.get_winner()

    @property
    def is_running(self) -> bool:
        """Check if the game is still running."""
        return self._is_running

    @property
    def error(self) -> Exception | None:
        """Get any error that occurred during the game."""
        return self._error

    # Input submission methods

    async def submit_action(self, action: PlayAction, timeout: float = 5.0) -> bool:
        """
        Submit a play action and wait for it to be processed.

        Returns True if processed successfully, False if timeout.
        """
        await self.interactive_agent.submit_action(action)
        return await self.interactive_agent.wait_for_processing(timeout)

    async def submit_draw(self, choice: DrawChoice, timeout: float = 5.0) -> bool:
        """
        Submit a draw choice and wait for it to be processed.

        Returns True if processed successfully, False if timeout.
        """
        await self.interactive_agent.submit_draw(choice)
        return await self.interactive_agent.wait_for_processing(timeout)

    async def submit_market_draw(self, market_index: int, timeout: float = 5.0) -> bool:
        """
        Submit a market draw with card selection as an atomic operation.

        This is the preferred way to draw from market - it queues both the
        draw choice and market card selection together.

        Returns True if processed successfully, False if timeout.
        """
        await self.interactive_agent.submit_market_draw(market_index)
        return await self.interactive_agent.wait_for_processing(timeout)

    async def submit_effect_choice(self, choice: Any, timeout: float = 5.0) -> bool:
        """
        Submit an effect choice and wait for it to be processed.

        Returns True if processed successfully, False if timeout.
        """
        await self.interactive_agent.submit_effect_choice(choice)
        return await self.interactive_agent.wait_for_processing(timeout)

    # State query methods

    def get_waiting_for(self) -> str | None:
        """Get what type of input the game is waiting for."""
        return self.interactive_agent.get_waiting_for()

    def get_last_effect_choice(self) -> EffectChoice | None:
        """Get the last effect choice that was requested."""
        return self.interactive_agent.last_effect_choice

    async def wait_for_ready(self, timeout: float = 5.0) -> bool:
        """
        Wait for the game to be ready for input.

        Returns True if ready, False if timeout.
        """
        return await self.interactive_agent.wait_for_waiting_state(timeout)

    def stop(self) -> None:
        """Stop the game."""
        self._is_running = False
        if self._game_task and not self._game_task.done():
            self._game_task.cancel()


class SessionManager:
    """
    Global manager for all active game sessions.
    """

    def __init__(self):
        self.sessions: Dict[str, GameSession] = {}

    async def create_game(
        self,
        opponent: Literal['random', 'greedy', 'lookahead'],
        seed: int | None = None,
        max_turns: int = 10,
    ) -> GameSession:
        """Create a new game session."""
        import uuid
        game_id = str(uuid.uuid4())

        session = GameSession(
            game_id=game_id,
            opponent=opponent,
            seed=seed,
            max_turns=max_turns,
        )

        self.sessions[game_id] = session
        await session.start()

        # Wait for game to be ready for first input
        await session.wait_for_ready(timeout=5.0)

        return session

    def get_game(self, game_id: str) -> GameSession | None:
        """Get a game session by ID."""
        return self.sessions.get(game_id)

    def delete_game(self, game_id: str) -> bool:
        """Delete a game session."""
        session = self.sessions.pop(game_id, None)
        if session:
            session.stop()
            return True
        return False

    def cleanup_finished_games(self) -> None:
        """Remove finished games from memory."""
        finished = [
            game_id for game_id, session in self.sessions.items()
            if not session.is_running
        ]
        for game_id in finished:
            session = self.sessions.pop(game_id)
            session.stop()


# Global session manager instance
session_manager = SessionManager()
