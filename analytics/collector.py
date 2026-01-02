"""Data collection during game simulations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.state import GameState


@dataclass
class CardPlayRecord:
    """Record of a single card play."""
    card_name: str
    player_idx: int
    turn: int
    points_scored: int = 0
    was_center_trigger: bool = False
    was_exit_trigger: bool = False


@dataclass
class GameRecord:
    """Complete record of a single game."""
    game_id: int
    winner: int | None  # 0, 1, or None for tie
    player0_score: int
    player1_score: int
    total_turns: int
    cards_played_p0: list[str] = field(default_factory=list)
    cards_played_p1: list[str] = field(default_factory=list)
    card_plays: list[CardPlayRecord] = field(default_factory=list)
    seed: int | None = None
    unique_cards_entered: int = 0  # Number of unique cards that entered play (25 - deck size)

    @property
    def score_margin(self) -> int:
        """Absolute difference in scores."""
        return abs(self.player0_score - self.player1_score)

    @property
    def first_player_won(self) -> bool | None:
        """Whether the first player (player 0) won."""
        return self.winner == 0 if self.winner is not None else None


class GameDataCollector:
    """Collects data from game simulations."""

    def __init__(self):
        self.games: list[GameRecord] = []
        self._next_game_id = 0

    def record_game(
        self,
        final_state: GameState,
        winner: int | None,
        seed: int | None = None,
    ) -> GameRecord:
        """
        Record a completed game.

        Args:
            final_state: The final game state
            winner: The winning player (0, 1, or None)
            seed: The random seed used for this game

        Returns:
            The created GameRecord
        """
        # Extract cards played by each player from the final state
        cards_p0 = [c.name for c in final_state.players[0].row]
        cards_p1 = [c.name for c in final_state.players[1].row]

        # Calculate unique cards that entered play (all cards not in deck)
        # Total deck is 25 cards, so unique entered = 25 - remaining in deck
        unique_cards_entered = 25 - len(final_state.deck)

        record = GameRecord(
            game_id=self._next_game_id,
            winner=winner,
            player0_score=final_state.players[0].score,
            player1_score=final_state.players[1].score,
            total_turns=final_state.turn_counter,
            cards_played_p0=cards_p0,
            cards_played_p1=cards_p1,
            seed=seed,
            unique_cards_entered=unique_cards_entered,
        )

        self.games.append(record)
        self._next_game_id += 1

        return record

    def to_dataframe(self):
        """Convert game records to a pandas DataFrame."""
        import pandas as pd

        data = []
        for game in self.games:
            data.append({
                "game_id": game.game_id,
                "winner": game.winner,
                "player0_score": game.player0_score,
                "player1_score": game.player1_score,
                "score_margin": game.score_margin,
                "total_turns": game.total_turns,
                "first_player_won": game.first_player_won,
                "unique_cards_entered": game.unique_cards_entered,
                "cards_p0": ",".join(game.cards_played_p0),
                "cards_p1": ",".join(game.cards_played_p1),
                "seed": game.seed,
            })

        return pd.DataFrame(data)

    def get_card_appearances(self) -> dict[str, dict[str, int]]:
        """
        Get card appearance statistics.

        Returns dict mapping card name -> {
            'times_in_winner_row': int,
            'times_in_loser_row': int,
            'times_in_p0_row': int,
            'times_in_p1_row': int,
        }
        """
        stats: dict[str, dict[str, int]] = {}

        for game in self.games:
            # Process player 0's cards
            for card_name in game.cards_played_p0:
                if card_name not in stats:
                    stats[card_name] = {
                        "times_in_winner_row": 0,
                        "times_in_loser_row": 0,
                        "times_in_p0_row": 0,
                        "times_in_p1_row": 0,
                        "times_in_tie_row": 0,
                    }
                stats[card_name]["times_in_p0_row"] += 1
                if game.winner == 0:
                    stats[card_name]["times_in_winner_row"] += 1
                elif game.winner == 1:
                    stats[card_name]["times_in_loser_row"] += 1
                else:
                    stats[card_name]["times_in_tie_row"] += 1

            # Process player 1's cards
            for card_name in game.cards_played_p1:
                if card_name not in stats:
                    stats[card_name] = {
                        "times_in_winner_row": 0,
                        "times_in_loser_row": 0,
                        "times_in_p0_row": 0,
                        "times_in_p1_row": 0,
                        "times_in_tie_row": 0,
                    }
                stats[card_name]["times_in_p1_row"] += 1
                if game.winner == 1:
                    stats[card_name]["times_in_winner_row"] += 1
                elif game.winner == 0:
                    stats[card_name]["times_in_loser_row"] += 1
                else:
                    stats[card_name]["times_in_tie_row"] += 1

        return stats

    def clear(self) -> None:
        """Clear all collected data."""
        self.games = []
        self._next_game_id = 0
