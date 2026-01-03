#!/usr/bin/env python3
"""CLI entry point for Robot Assembly Line simulation."""

from __future__ import annotations

import asyncio
import sys
from multiprocessing import Pool, cpu_count
from typing import Any

import click
from tqdm import tqdm

from game.engine import GameEngine
from game.cards import get_all_cards
from agents.random_agent import RandomAgent
from agents.greedy_agent import GreedyAgent
from agents.lookahead_agent import LookaheadAgent
from analytics.collector import GameDataCollector
from analytics.metrics import calculate_metrics
from analytics.reports import (
    print_summary_report,
    generate_card_report,
    export_to_csv,
    create_visualizations,
)


def _create_agent(agent_type: str, seed: int | None):
    """
    Create an agent of the specified type.

    Supported formats:
    - "random" - RandomAgent
    - "greedy" - GreedyAgent
    - "lookahead" or "lookahead:N" - LookaheadAgent with depth N (default 2)
    """
    if agent_type == "greedy":
        return GreedyAgent(seed=seed)
    elif agent_type.startswith("lookahead"):
        # Parse depth from "lookahead:N" format
        parts = agent_type.split(":")
        depth = int(parts[1]) if len(parts) > 1 else 2
        return LookaheadAgent(seed=seed, depth=depth)
    return RandomAgent(seed=seed)


def run_single_game(args: tuple[int, int | None, int, str, str]) -> dict[str, Any]:
    """
    Run a single game and return the results.

    Args:
        args: Tuple of (game_index, seed, max_turns, agent0_type, agent1_type)

    Returns:
        Dict with game results (agent-based, not position-based)
    """
    game_idx, base_seed, max_turns, agent0_type, agent1_type = args

    # Create unique seed for this game
    seed = base_seed + game_idx if base_seed is not None else None

    import random
    rng = random.Random(seed)

    # Randomize player positions (50/50 for each game)
    swap_positions = rng.choice([True, False])

    # Create agents with their own seeds
    agent0 = _create_agent(agent0_type, seed)
    agent1 = _create_agent(agent1_type, seed + 1000000 if seed else None)

    # Assign to positions
    if swap_positions:
        # agent0 is P1 (second), agent1 is P0 (first)
        agents = (agent1, agent0)
        agent0_position = 1
    else:
        # agent0 is P0 (first), agent1 is P1 (second)
        agents = (agent0, agent1)
        agent0_position = 0

    # Run game
    engine = GameEngine(
        agents=agents,
        seed=seed,
        max_turns=max_turns,
    )

    final_state = asyncio.run(engine.run_game())
    winner = engine.get_winner()

    # Map position-based winner to agent-based winner
    if winner is None:
        agent_winner = None
    elif winner == agent0_position:
        agent_winner = 0  # agent0 won
    else:
        agent_winner = 1  # agent1 won

    # Calculate unique cards entered (total cards - remaining in deck)
    from game.cards import CARD_REGISTRY
    unique_cards_entered = len(CARD_REGISTRY) - len(final_state.deck)

    # Get scores by agent (not by position)
    agent0_score = final_state.players[agent0_position].score
    agent1_score = final_state.players[1 - agent0_position].score

    return {
        "winner": agent_winner,  # Which agent won (0, 1, or None)
        "agent0_score": agent0_score,
        "agent1_score": agent1_score,
        "total_turns": final_state.turn_counter,
        "cards_agent0": [c.name for c in final_state.players[agent0_position].row],
        "cards_agent1": [c.name for c in final_state.players[1 - agent0_position].row],
        "seed": seed,
        "unique_cards_entered": unique_cards_entered,
        "position_winner": winner,  # Position-based winner for first-player advantage
        "card_scores": dict(final_state.card_scores),  # Points scored by each card
    }


@click.group()
def cli():
    """Robot Assembly Line - Automated Playtesting Tool."""
    pass


@cli.command()
@click.option(
    "--games", "-n",
    default=1000,
    help="Number of games to simulate",
)
@click.option(
    "--seed", "-s",
    default=None,
    type=int,
    help="Random seed for reproducibility",
)
@click.option(
    "--parallel/--no-parallel",
    default=True,
    help="Use parallel processing",
)
@click.option(
    "--workers", "-w",
    default=None,
    type=int,
    help="Number of worker processes (default: CPU count)",
)
@click.option(
    "--output", "-o",
    default=None,
    help="Output CSV file for detailed results",
)
@click.option(
    "--charts", "-c",
    default=None,
    help="Output directory for visualization charts",
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Suppress progress bar",
)
@click.option(
    "--turns", "-t",
    default=10,
    type=int,
    help="Number of turns per game (default: 10)",
)
@click.option(
    "--agent0", "-a0",
    default="random",
    type=str,
    help="Agent type for player 0 (random, greedy, lookahead, lookahead:N)",
)
@click.option(
    "--agent1", "-a1",
    default="random",
    type=str,
    help="Agent type for player 1 (random, greedy, lookahead, lookahead:N)",
)
def simulate(
    games: int,
    seed: int | None,
    parallel: bool,
    workers: int | None,
    output: str | None,
    charts: str | None,
    quiet: bool,
    turns: int,
    agent0: str,
    agent1: str,
):
    """Run a simulation of many games."""
    click.echo(f"Running {games:,} games: {agent0} vs {agent1}...")

    collector = GameDataCollector()

    if parallel and games > 10:
        # Parallel execution
        num_workers = workers or cpu_count()
        args = [(i, seed, turns, agent0, agent1) for i in range(games)]

        with Pool(num_workers) as pool:
            if quiet:
                results = pool.map(run_single_game, args)
            else:
                results = list(tqdm(
                    pool.imap(run_single_game, args),
                    total=games,
                    desc="Simulating",
                ))

        # Collect results (now agent-based)
        for result in results:
            from analytics.collector import GameRecord
            record = GameRecord(
                game_id=collector._next_game_id,
                winner=result["winner"],  # agent winner (0 or 1)
                player0_score=result["agent0_score"],
                player1_score=result["agent1_score"],
                total_turns=result["total_turns"],
                cards_played_p0=result["cards_agent0"],
                cards_played_p1=result["cards_agent1"],
                seed=result["seed"],
                unique_cards_entered=result["unique_cards_entered"],
                position_winner=result["position_winner"],  # for first-player advantage
                card_scores=result["card_scores"],  # points scored by each card
            )
            collector.games.append(record)
            collector._next_game_id += 1
    else:
        # Sequential execution
        iterator = range(games)
        if not quiet:
            iterator = tqdm(iterator, desc="Simulating")

        for i in iterator:
            game_seed = seed + i if seed is not None else None

            import random
            rng = random.Random(game_seed)

            # Randomize player positions
            swap_positions = rng.choice([True, False])

            a0 = _create_agent(agent0, game_seed)
            a1 = _create_agent(agent1, game_seed + 1000000 if game_seed else None)

            # Assign to positions
            if swap_positions:
                agents = (a1, a0)
                agent0_position = 1
            else:
                agents = (a0, a1)
                agent0_position = 0

            engine = GameEngine(
                agents=agents,
                seed=game_seed,
                max_turns=turns,
            )

            final_state = asyncio.run(engine.run_game())
            winner = engine.get_winner()

            # Map position-based winner to agent-based winner
            if winner is None:
                agent_winner = None
            elif winner == agent0_position:
                agent_winner = 0
            else:
                agent_winner = 1

            # Create game record with agent-based data
            from analytics.collector import GameRecord
            agent0_score = final_state.players[agent0_position].score
            agent1_score = final_state.players[1 - agent0_position].score
            from game.cards import CARD_REGISTRY
            unique_cards_entered = len(CARD_REGISTRY) - len(final_state.deck)

            record = GameRecord(
                game_id=collector._next_game_id,
                winner=agent_winner,
                player0_score=agent0_score,
                player1_score=agent1_score,
                total_turns=final_state.turn_counter,
                cards_played_p0=[c.name for c in final_state.players[agent0_position].row],
                cards_played_p1=[c.name for c in final_state.players[1 - agent0_position].row],
                seed=game_seed,
                unique_cards_entered=unique_cards_entered,
                position_winner=winner,  # for first-player advantage
                card_scores=dict(final_state.card_scores),  # points scored by each card
            )
            collector.games.append(record)
            collector._next_game_id += 1

    # Calculate metrics
    metrics = calculate_metrics(collector)

    # Print report
    click.echo()
    print_summary_report(metrics)

    # Card report
    click.echo()
    click.echo(generate_card_report(metrics))

    # Export CSV if requested
    if output:
        export_to_csv(metrics, output)
        click.echo(f"\nCard metrics exported to {output}")

    # Generate charts if requested
    if charts:
        create_visualizations(metrics, charts)


@cli.command()
@click.option(
    "--games", "-n",
    default=100,
    help="Number of games per test",
)
@click.option(
    "--seed", "-s",
    default=42,
    type=int,
    help="Random seed",
)
@click.option(
    "--turns", "-t",
    default=10,
    type=int,
    help="Number of turns per game",
)
def quick_test(games: int, seed: int, turns: int):
    """Run a quick test to verify the simulation works."""
    click.echo(f"Running quick test with {games} games...")

    collector = GameDataCollector()

    for i in tqdm(range(games), desc="Testing"):
        game_seed = seed + i
        agent0 = RandomAgent(seed=game_seed)
        agent1 = RandomAgent(seed=game_seed + 1000000)

        try:
            engine = GameEngine(
                agents=(agent0, agent1),
                seed=game_seed,
                max_turns=turns,
            )
            final_state = asyncio.run(engine.run_game())
            winner = engine.get_winner()
            collector.record_game(final_state, winner, seed=game_seed)
        except Exception as e:
            click.echo(f"\nError in game {i}: {e}")
            raise

    metrics = calculate_metrics(collector)

    click.echo(f"\nTest completed successfully!")
    click.echo(f"P0 wins: {metrics.player0_wins}, P1 wins: {metrics.player1_wins}, Ties: {metrics.ties}")
    click.echo(f"First player win rate: {metrics.first_player_win_rate:.1%}")


@cli.command()
@click.option(
    "--seed", "-s",
    default=None,
    type=int,
    help="Random seed for reproducibility",
)
@click.option(
    "--turns", "-t",
    default=10,
    type=int,
    help="Number of turns per game",
)
@click.option(
    "--delay", "-d",
    default=0.3,
    type=float,
    help="Delay between actions in seconds (0 for instant)",
)
@click.option(
    "--no-delay",
    is_flag=True,
    help="Run without delays (same as --delay 0)",
)
@click.option(
    "--agent0", "-a0",
    default="random",
    type=str,
    help="Agent type for player 0 (random, greedy, lookahead, lookahead:N)",
)
@click.option(
    "--agent1", "-a1",
    default="random",
    type=str,
    help="Agent type for player 1 (random, greedy, lookahead, lookahead:N)",
)
def demo(seed: int | None, turns: int, delay: float, no_delay: bool, agent0: str, agent1: str):
    """Run a demo game with step-by-step visualization."""
    from game.demo import DemoEngine

    actual_delay = 0 if no_delay else delay

    if seed is None:
        import random
        seed = random.randint(0, 999999)

    click.echo(f"Starting demo game (seed: {seed}, turns: {turns})")
    click.echo(f"P0: {agent0}, P1: {agent1}")
    click.echo("Press Ctrl+C to exit at any time")
    click.echo("")

    a0 = _create_agent(agent0, seed)
    a1 = _create_agent(agent1, seed + 1000000)

    try:
        engine = DemoEngine(
            agents=(a0, a1),
            seed=seed,
            max_turns=turns,
            delay=actual_delay,
        )
        engine.run_demo()
    except KeyboardInterrupt:
        click.echo("\n\nDemo interrupted.")


@cli.command()
def list_cards():
    """List all cards in the game."""
    cards = get_all_cards()

    click.echo("=" * 50)
    click.echo("CARD LIST")
    click.echo("=" * 50)

    from game.state import CardType

    for card_type in CardType:
        type_cards = [c for c in cards if c.card_type == card_type]
        click.echo(f"\n{card_type.name} CARDS ({len(type_cards)})")
        click.echo("-" * 40)
        for card in type_cards:
            icon_str = card.icon.name if card.icon else "None"
            click.echo(f"  {card.name:<20} [{icon_str}]")


if __name__ == "__main__":
    cli()
