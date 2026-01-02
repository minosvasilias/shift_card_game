"""Metric calculations for simulation analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .collector import GameDataCollector


@dataclass
class CardMetrics:
    """Metrics for a single card."""
    name: str
    times_appeared: int = 0
    times_in_winner_row: int = 0
    times_in_loser_row: int = 0
    win_rate: float = 0.0  # When this card is in final row, how often did that player win

    @property
    def appearance_rate(self) -> float:
        """Rate this card appears in any player's final row."""
        return self.times_appeared

    def __str__(self) -> str:
        return (
            f"{self.name}: appeared={self.times_appeared}, "
            f"win_rate={self.win_rate:.1%}"
        )


@dataclass
class SimulationMetrics:
    """Aggregate metrics for a simulation run."""
    total_games: int = 0
    player0_wins: int = 0
    player1_wins: int = 0
    ties: int = 0
    avg_score_p0: float = 0.0
    avg_score_p1: float = 0.0
    avg_score_margin: float = 0.0
    avg_turns: float = 0.0
    first_player_win_rate: float = 0.0
    card_metrics: dict[str, CardMetrics] = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"Games: {self.total_games}\n"
            f"P0 wins: {self.player0_wins} ({self.player0_wins/self.total_games:.1%})\n"
            f"P1 wins: {self.player1_wins} ({self.player1_wins/self.total_games:.1%})\n"
            f"Ties: {self.ties} ({self.ties/self.total_games:.1%})\n"
            f"First player advantage: {self.first_player_win_rate:.1%}\n"
            f"Avg scores: P0={self.avg_score_p0:.1f}, P1={self.avg_score_p1:.1f}\n"
            f"Avg margin: {self.avg_score_margin:.1f}\n"
            f"Avg turns: {self.avg_turns:.1f}"
        )


def calculate_metrics(collector: GameDataCollector) -> SimulationMetrics:
    """
    Calculate aggregate metrics from collected game data.

    Args:
        collector: GameDataCollector with recorded games

    Returns:
        SimulationMetrics with calculated statistics
    """
    games = collector.games

    if not games:
        return SimulationMetrics()

    total_games = len(games)
    player0_wins = sum(1 for g in games if g.winner == 0)
    player1_wins = sum(1 for g in games if g.winner == 1)
    ties = sum(1 for g in games if g.winner is None)

    avg_score_p0 = sum(g.player0_score for g in games) / total_games
    avg_score_p1 = sum(g.player1_score for g in games) / total_games
    avg_margin = sum(g.score_margin for g in games) / total_games
    avg_turns = sum(g.total_turns for g in games) / total_games

    # First player win rate (excluding ties)
    decisive_games = total_games - ties
    first_player_win_rate = player0_wins / decisive_games if decisive_games > 0 else 0.5

    # Card metrics
    card_stats = collector.get_card_appearances()
    card_metrics: dict[str, CardMetrics] = {}

    for card_name, stats in card_stats.items():
        times_appeared = stats["times_in_p0_row"] + stats["times_in_p1_row"]
        times_winner = stats["times_in_winner_row"]
        times_loser = stats["times_in_loser_row"]

        # Win rate = times in winner's row / (times in winner's row + times in loser's row)
        decisive_appearances = times_winner + times_loser
        win_rate = times_winner / decisive_appearances if decisive_appearances > 0 else 0.5

        card_metrics[card_name] = CardMetrics(
            name=card_name,
            times_appeared=times_appeared,
            times_in_winner_row=times_winner,
            times_in_loser_row=times_loser,
            win_rate=win_rate,
        )

    return SimulationMetrics(
        total_games=total_games,
        player0_wins=player0_wins,
        player1_wins=player1_wins,
        ties=ties,
        avg_score_p0=avg_score_p0,
        avg_score_p1=avg_score_p1,
        avg_score_margin=avg_margin,
        avg_turns=avg_turns,
        first_player_win_rate=first_player_win_rate,
        card_metrics=card_metrics,
    )


def get_top_cards(
    metrics: SimulationMetrics,
    n: int = 10,
    by: str = "win_rate",
    min_appearances: int = 10,
) -> list[CardMetrics]:
    """
    Get the top N cards by a given metric.

    Args:
        metrics: SimulationMetrics with card data
        n: Number of cards to return
        by: Metric to sort by ("win_rate" or "times_appeared")
        min_appearances: Minimum appearances to be included

    Returns:
        List of top CardMetrics
    """
    filtered = [
        cm for cm in metrics.card_metrics.values()
        if cm.times_appeared >= min_appearances
    ]

    if by == "win_rate":
        filtered.sort(key=lambda x: x.win_rate, reverse=True)
    elif by == "times_appeared":
        filtered.sort(key=lambda x: x.times_appeared, reverse=True)

    return filtered[:n]


def get_bottom_cards(
    metrics: SimulationMetrics,
    n: int = 10,
    by: str = "win_rate",
    min_appearances: int = 10,
) -> list[CardMetrics]:
    """
    Get the bottom N cards by a given metric.

    Args:
        metrics: SimulationMetrics with card data
        n: Number of cards to return
        by: Metric to sort by ("win_rate" or "times_appeared")
        min_appearances: Minimum appearances to be included

    Returns:
        List of bottom CardMetrics
    """
    filtered = [
        cm for cm in metrics.card_metrics.values()
        if cm.times_appeared >= min_appearances
    ]

    if by == "win_rate":
        filtered.sort(key=lambda x: x.win_rate)
    elif by == "times_appeared":
        filtered.sort(key=lambda x: x.times_appeared)

    return filtered[:n]
