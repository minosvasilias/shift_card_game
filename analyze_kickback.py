"""Analyze Kickback usage patterns to understand why it underperforms."""

import asyncio
from game.engine import GameEngine
from game.cards import CARD_REGISTRY, get_all_cards
from game.state import CardType
from agents.lookahead_agent import LookaheadAgent
from collections import defaultdict


async def track_kickback_game_async(seed, verbose=False):
    """
    Track a single game and record Kickback behavior.

    Returns dict with:
    - kickback_triggered: number of times Kickback triggered
    - kickback_consecutive: number of consecutive triggers
    - exit_cards_in_deck: how many exit cards were available
    - kickback_holder_won: did the player with Kickback win?
    - kickback_final_position: where was Kickback at game end?
    """
    agent0 = LookaheadAgent(seed=seed, depth=3)
    agent1 = LookaheadAgent(seed=seed + 1000000, depth=3)

    engine = GameEngine(
        agents=(agent0, agent1),
        seed=seed,
        max_turns=10,
    )

    # Track game events
    kickback_stats = {
        'kickback_appeared': False,
        'kickback_player': None,
        'kickback_triggers': 0,
        'consecutive_triggers': 0,
        'points_from_kickback': 0,
        'exit_cards_available': 0,
        'kickback_holder_won': False,
        'final_position': None,
        'max_row_length_when_triggered': 0,
    }

    last_trigger_turn = -999

    # Run game turn by turn
    turn = 0
    while not engine.state.game_over and turn < 20:
        player_idx = engine.state.current_player
        player = engine.state.players[player_idx]

        # Check for Kickback before turn
        for card_idx, card in enumerate(player.row):
            if card.name == "Kickback":
                kickback_stats['kickback_appeared'] = True
                kickback_stats['kickback_player'] = player_idx

                # Check if it's in center and will trigger
                if card_idx == 1 and len(player.row) == 3 and card.face_up:
                    kickback_stats['kickback_triggers'] += 1

                    # Check if consecutive
                    if turn - last_trigger_turn == 2:  # One round later
                        kickback_stats['consecutive_triggers'] += 1

                    last_trigger_turn = turn
                    kickback_stats['max_row_length_when_triggered'] = max(
                        kickback_stats['max_row_length_when_triggered'],
                        len(player.row)
                    )

        # Count exit cards in hand/market
        exit_count = 0
        for card in player.hand:
            if card.card_type == CardType.EXIT:
                exit_count += 1
        for card in engine.state.market:
            if card.card_type == CardType.EXIT:
                exit_count += 1
        kickback_stats['exit_cards_available'] = max(
            kickback_stats['exit_cards_available'],
            exit_count
        )

        # Play turn
        await engine.play_turn()
        turn += 1

    # Check final state
    if kickback_stats['kickback_appeared']:
        kickback_player = kickback_stats['kickback_player']
        winner = engine.get_winner()

        if winner == kickback_player:
            kickback_stats['kickback_holder_won'] = True

        # Find final position
        for idx, card in enumerate(engine.state.players[kickback_player].row):
            if card.name == "Kickback":
                kickback_stats['final_position'] = idx
                break

    return kickback_stats


def track_kickback_game(seed, verbose=False):
    """Sync wrapper for async function."""
    return asyncio.run(track_kickback_game_async(seed, verbose))


async def analyze_kickback_performance_async(num_games=100, seed=42):
    """Run multiple games and analyze Kickback patterns."""
    print("=== ANALYZING KICKBACK PERFORMANCE ===\n")
    print(f"Running {num_games} games with lookahead:3 agents...\n")

    all_stats = []
    games_with_kickback = 0

    for i in range(num_games):
        stats = await track_kickback_game_async(seed + i)
        all_stats.append(stats)
        if stats['kickback_appeared']:
            games_with_kickback += 1

    print(f"Games with Kickback: {games_with_kickback}/{num_games} ({games_with_kickback/num_games*100:.1f}%)\n")

    if games_with_kickback == 0:
        print("No Kickback appearances to analyze!")
        return

    # Analyze Kickback games
    total_triggers = sum(s['kickback_triggers'] for s in all_stats if s['kickback_appeared'])
    total_consecutive = sum(s['consecutive_triggers'] for s in all_stats if s['kickback_appeared'])
    wins_with_kickback = sum(s['kickback_holder_won'] for s in all_stats if s['kickback_appeared'])

    avg_triggers = total_triggers / games_with_kickback
    avg_consecutive = total_consecutive / games_with_kickback
    win_rate = wins_with_kickback / games_with_kickback * 100

    print("TRIGGER ANALYSIS:")
    print("-" * 50)
    print(f"Average triggers per game: {avg_triggers:.2f}")
    print(f"Average consecutive triggers: {avg_consecutive:.2f}")
    print(f"Total triggers: {total_triggers}")
    print(f"Total consecutive triggers: {total_consecutive}")
    print()

    print("WIN RATE:")
    print("-" * 50)
    print(f"Win rate when Kickback appears: {win_rate:.1f}%")
    print(f"Games won with Kickback: {wins_with_kickback}/{games_with_kickback}")
    print()

    # Trigger distribution
    trigger_counts = defaultdict(int)
    for s in all_stats:
        if s['kickback_appeared']:
            trigger_counts[s['kickback_triggers']] += 1

    print("TRIGGER DISTRIBUTION:")
    print("-" * 50)
    for count in sorted(trigger_counts.keys()):
        pct = trigger_counts[count] / games_with_kickback * 100
        print(f"  {count} triggers: {trigger_counts[count]} games ({pct:.1f}%)")
    print()

    # Exit card availability
    avg_exit_cards = sum(s['exit_cards_available'] for s in all_stats if s['kickback_appeared']) / games_with_kickback
    print("EXIT CARD SYNERGY:")
    print("-" * 50)
    print(f"Average exit cards available: {avg_exit_cards:.2f}")
    print()

    # Detailed examples
    print("EXAMPLE SCENARIOS:")
    print("-" * 50)

    # Find games with multiple triggers
    multi_trigger_games = [s for s in all_stats if s['kickback_triggers'] >= 2]
    if multi_trigger_games:
        print(f"\n{len(multi_trigger_games)} games with 2+ triggers:")
        for i, s in enumerate(multi_trigger_games[:5]):  # Show first 5
            won_str = "WON" if s['kickback_holder_won'] else "LOST"
            print(f"  Game: {s['kickback_triggers']} triggers, {s['consecutive_triggers']} consecutive → {won_str}")

    # Find games with no triggers
    no_trigger_games = [s for s in all_stats if s['kickback_appeared'] and s['kickback_triggers'] == 0]
    if no_trigger_games:
        print(f"\n{len(no_trigger_games)} games where Kickback appeared but NEVER triggered:")
        avg_win_no_trigger = sum(s['kickback_holder_won'] for s in no_trigger_games) / len(no_trigger_games) * 100
        print(f"  Win rate when never triggered: {avg_win_no_trigger:.1f}%")

    print("\n" + "=" * 50)
    print("CONCLUSIONS:")
    print("=" * 50)

    if avg_triggers < 1:
        print("⚠️  Kickback triggers less than once per game on average!")
        print("   This suggests it's hard to set up the combo.")

    if avg_consecutive < 0.5:
        print("⚠️  Consecutive triggers are rare!")
        print("   The theoretical power isn't realized in practice.")

    if win_rate < 40:
        print("⚠️  Low win rate suggests Kickback hurts the player!")
        print("   The tempo loss may outweigh the points.")

    print()


def analyze_kickback_performance(num_games=100, seed=42):
    """Sync wrapper for async function."""
    asyncio.run(analyze_kickback_performance_async(num_games, seed))


if __name__ == "__main__":
    analyze_kickback_performance(num_games=100, seed=42)
