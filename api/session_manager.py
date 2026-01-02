"""
Game session manager for tracking and running interactive games.
"""

import uuid
import threading
from typing import Dict, Literal
from game.engine import GameEngine
from game.state import GameState, PlayAction, DrawChoice, EffectChoice, Side
from agents.interactive_agent import InteractiveAgent
from agents.random_agent import RandomAgent
from agents.greedy_agent import GreedyAgent
from agents.lookahead_agent import LookaheadAgent


class GameSession:
    """
    Manages a single game session with an interactive player.
    Runs the game in a background thread.
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

        self.lock = threading.Lock()
        self.game_thread: threading.Thread | None = None
        self.is_running = False
        self.error: Exception | None = None

    def start(self) -> None:
        """Start the game in a background thread."""
        self.is_running = True
        self.game_thread = threading.Thread(target=self._run_game, daemon=True)
        self.game_thread.start()

    def _run_game(self) -> None:
        """Run the game loop in a background thread."""
        try:
            while self.is_running:
                with self.lock:
                    if self.engine.state.game_over:
                        self.is_running = False
                        break

                # play_turn() will block when waiting for interactive player input
                continue_game = self.engine.play_turn()

                if not continue_game:
                    with self.lock:
                        self.is_running = False
                    break
        except Exception as e:
            self.error = e
            self.is_running = False

    def get_state(self) -> GameState:
        """Get the current game state (thread-safe)."""
        with self.lock:
            # Return a copy to avoid mutation issues
            return self.engine.state.copy()

    def get_winner(self) -> int | None:
        """Get the winner of the game (thread-safe)."""
        with self.lock:
            return self.engine.get_winner()

    def submit_action(self, action: PlayAction) -> None:
        """Submit a play action for the interactive player."""
        self.interactive_agent.submit_action(action)

    def submit_draw(self, choice: DrawChoice, market_index: int | None = None) -> None:
        """Submit a draw choice for the interactive player."""
        # If drawing from market, we need to store the market index somehow
        # The DrawChoice enum doesn't have this info, so we need to handle it
        # Looking at the engine code, draw choice is handled differently
        # Let me check how draws work...
        # Actually, DrawChoice is just DECK or MARKET, and if MARKET, the agent
        # chooses which card via choose_effect_option with MARKET_CARD choice
        self.interactive_agent.submit_draw(choice)

    def submit_effect_choice(self, choice: any) -> None:
        """Submit an effect choice for the interactive player."""
        self.interactive_agent.submit_effect_choice(choice)

    def is_waiting_for_input(self) -> bool:
        """Check if the game is waiting for interactive player input."""
        return self.interactive_agent.is_waiting()

    def get_waiting_for(self) -> str | None:
        """Get what type of input the game is waiting for."""
        return self.interactive_agent.get_waiting_for()

    def get_last_effect_choice(self) -> EffectChoice | None:
        """Get the last effect choice that was requested."""
        return self.interactive_agent.last_effect_choice

    def stop(self) -> None:
        """Stop the game thread."""
        self.is_running = False
        if self.game_thread and self.game_thread.is_alive():
            self.game_thread.join(timeout=5)


class SessionManager:
    """
    Global manager for all active game sessions.
    """

    def __init__(self):
        self.sessions: Dict[str, GameSession] = {}
        self.lock = threading.Lock()

    def create_game(
        self,
        opponent: Literal['random', 'greedy', 'lookahead'],
        seed: int | None = None,
        max_turns: int = 10,
    ) -> GameSession:
        """Create a new game session."""
        game_id = str(uuid.uuid4())

        session = GameSession(
            game_id=game_id,
            opponent=opponent,
            seed=seed,
            max_turns=max_turns,
        )

        with self.lock:
            self.sessions[game_id] = session

        session.start()
        return session

    def get_game(self, game_id: str) -> GameSession | None:
        """Get a game session by ID."""
        with self.lock:
            return self.sessions.get(game_id)

    def delete_game(self, game_id: str) -> bool:
        """Delete a game session."""
        with self.lock:
            session = self.sessions.pop(game_id, None)
            if session:
                session.stop()
                return True
            return False

    def cleanup_finished_games(self) -> None:
        """Remove finished games from memory."""
        with self.lock:
            finished = [
                game_id for game_id, session in self.sessions.items()
                if not session.is_running
            ]
            for game_id in finished:
                session = self.sessions.pop(game_id)
                session.stop()


# Global session manager instance
session_manager = SessionManager()
