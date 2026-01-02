"""Report generation for simulation results."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .metrics import SimulationMetrics, CardMetrics


def print_summary_report(metrics: SimulationMetrics) -> None:
    """Print a summary report to the console."""
    print("=" * 60)
    print("ROBOT ASSEMBLY LINE - SIMULATION REPORT")
    print("=" * 60)
    print()

    print("OVERVIEW")
    print("-" * 40)
    print(f"Total games:         {metrics.total_games:,}")
    print(f"Player 0 wins:       {metrics.player0_wins:,} ({metrics.player0_wins/metrics.total_games:.1%})")
    print(f"Player 1 wins:       {metrics.player1_wins:,} ({metrics.player1_wins/metrics.total_games:.1%})")
    print(f"Ties:                {metrics.ties:,} ({metrics.ties/metrics.total_games:.1%})")
    print()

    print("FIRST PLAYER ADVANTAGE")
    print("-" * 40)
    advantage = metrics.first_player_win_rate - 0.5
    advantage_str = f"+{advantage:.1%}" if advantage > 0 else f"{advantage:.1%}"
    print(f"First player win rate: {metrics.first_player_win_rate:.1%} ({advantage_str} advantage)")
    print()

    print("SCORING")
    print("-" * 40)
    print(f"Avg score (P0):      {metrics.avg_score_p0:.1f}")
    print(f"Avg score (P1):      {metrics.avg_score_p1:.1f}")
    print(f"Avg score margin:    {metrics.avg_score_margin:.1f}")
    print(f"Avg game length:     {metrics.avg_turns:.1f} turns")
    print()


def generate_card_report(
    metrics: SimulationMetrics,
    min_appearances: int = 10,
) -> str:
    """
    Generate a detailed card performance report.

    Args:
        metrics: SimulationMetrics with card data
        min_appearances: Minimum appearances to include a card

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 70)
    lines.append("CARD PERFORMANCE REPORT")
    lines.append("=" * 70)
    lines.append("")

    # Sort cards by win rate
    cards = list(metrics.card_metrics.values())
    cards = [c for c in cards if c.times_appeared >= min_appearances]
    cards.sort(key=lambda x: x.win_rate, reverse=True)

    if not cards:
        lines.append("No cards with sufficient data.")
        return "\n".join(lines)

    # Header
    lines.append(f"{'Card Name':<25} {'Appearances':>12} {'Win Rate':>10} {'Impact':>10}")
    lines.append("-" * 70)

    for card in cards:
        # Impact = deviation from 50% baseline
        impact = card.win_rate - 0.5
        impact_str = f"+{impact:.1%}" if impact > 0 else f"{impact:.1%}"

        lines.append(
            f"{card.name:<25} {card.times_appeared:>12} "
            f"{card.win_rate:>9.1%} {impact_str:>10}"
        )

    lines.append("")
    lines.append("TOP 5 CARDS (by win rate)")
    lines.append("-" * 40)
    for card in cards[:5]:
        lines.append(f"  {card.name}: {card.win_rate:.1%}")

    lines.append("")
    lines.append("BOTTOM 5 CARDS (by win rate)")
    lines.append("-" * 40)
    for card in cards[-5:]:
        lines.append(f"  {card.name}: {card.win_rate:.1%}")

    return "\n".join(lines)


def export_to_csv(metrics: SimulationMetrics, filepath: str) -> None:
    """
    Export card metrics to a CSV file.

    Args:
        metrics: SimulationMetrics with card data
        filepath: Path to write CSV file
    """
    import csv

    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'card_name',
            'times_appeared',
            'times_in_winner_row',
            'times_in_loser_row',
            'win_rate',
            'impact',
        ])

        for card in sorted(metrics.card_metrics.values(), key=lambda x: x.name):
            writer.writerow([
                card.name,
                card.times_appeared,
                card.times_in_winner_row,
                card.times_in_loser_row,
                f"{card.win_rate:.4f}",
                f"{card.win_rate - 0.5:.4f}",
            ])


def create_visualizations(
    metrics: SimulationMetrics,
    output_dir: str = ".",
) -> None:
    """
    Create matplotlib visualizations for the simulation results.

    Args:
        metrics: SimulationMetrics with data
        output_dir: Directory to save figures
    """
    import matplotlib.pyplot as plt
    import os

    os.makedirs(output_dir, exist_ok=True)

    # 1. Win rate distribution
    fig, ax = plt.subplots(figsize=(10, 6))

    cards = list(metrics.card_metrics.values())
    cards = [c for c in cards if c.times_appeared >= 10]
    cards.sort(key=lambda x: x.win_rate, reverse=True)

    names = [c.name for c in cards]
    win_rates = [c.win_rate for c in cards]
    colors = ['green' if wr > 0.5 else 'red' if wr < 0.5 else 'gray' for wr in win_rates]

    ax.barh(names, win_rates, color=colors, alpha=0.7)
    ax.axvline(x=0.5, color='black', linestyle='--', linewidth=1, label='Baseline (50%)')
    ax.set_xlabel('Win Rate')
    ax.set_title('Card Win Rates')
    ax.set_xlim(0, 1)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'card_win_rates.png'), dpi=150)
    plt.close()

    # 2. First player advantage pie chart
    fig, ax = plt.subplots(figsize=(8, 8))

    labels = ['Player 0 (First)', 'Player 1 (Second)', 'Tie']
    sizes = [metrics.player0_wins, metrics.player1_wins, metrics.ties]
    colors_pie = ['#2ecc71', '#e74c3c', '#95a5a6']
    explode = (0.05, 0, 0)

    ax.pie(sizes, explode=explode, labels=labels, colors=colors_pie,
           autopct='%1.1f%%', shadow=True, startangle=90)
    ax.set_title('Game Outcomes')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'game_outcomes.png'), dpi=150)
    plt.close()

    # 3. Card appearance frequency
    fig, ax = plt.subplots(figsize=(10, 6))

    cards_by_appearance = sorted(cards, key=lambda x: x.times_appeared, reverse=True)
    names = [c.name for c in cards_by_appearance[:15]]
    appearances = [c.times_appeared for c in cards_by_appearance[:15]]

    ax.barh(names, appearances, color='steelblue', alpha=0.7)
    ax.set_xlabel('Times Appeared in Final Row')
    ax.set_title('Most Common Cards in Final Rows')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'card_appearances.png'), dpi=150)
    plt.close()

    print(f"Visualizations saved to {output_dir}/")
