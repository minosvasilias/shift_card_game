#!/usr/bin/env python3
"""Diagnostic test to verify position randomization and metrics."""

from analytics.collector import GameDataCollector, GameRecord

# Create test data with known position outcomes
collector = GameDataCollector()

# Game 1: Position 0 (first) wins
collector.games.append(GameRecord(
    game_id=0,
    winner=0,  # agent0 won
    player0_score=10,
    player1_score=5,
    total_turns=5,
    position_winner=0,  # Position 0 (first player) won
    unique_cards_entered=25,
))

# Game 2: Position 1 (second) wins
collector.games.append(GameRecord(
    game_id=1,
    winner=1,  # agent1 won
    player0_score=5,
    player1_score=10,
    total_turns=5,
    position_winner=1,  # Position 1 (second player) won
    unique_cards_entered=25,
))

# Game 3: Position 0 (first) wins
collector.games.append(GameRecord(
    game_id=2,
    winner=1,  # agent1 won (was first player)
    player0_score=5,
    player1_score=10,
    total_turns=5,
    position_winner=0,  # Position 0 (first player) won
    unique_cards_entered=25,
))

# Game 4: Position 1 (second) wins
collector.games.append(GameRecord(
    game_id=3,
    winner=0,  # agent0 won (was second player)
    player0_score=10,
    player1_score=5,
    total_turns=5,
    position_winner=1,  # Position 1 (second player) won
    unique_cards_entered=25,
))

from analytics.metrics import calculate_metrics

metrics = calculate_metrics(collector)

print("=== DIAGNOSTIC TEST RESULTS ===")
print(f"Total games: {metrics.total_games}")
print(f"Agent0 wins: {metrics.player0_wins}")
print(f"Agent1 wins: {metrics.player1_wins}")
print(f"First player win rate: {metrics.first_player_win_rate:.1%}")
print()
print("EXPECTED: First player win rate should be 50.0% (2 out of 4)")
print(f"ACTUAL: {metrics.first_player_win_rate:.1%}")
print()
if abs(metrics.first_player_win_rate - 0.5) < 0.01:
    print("✅ PASS: First player advantage calculation is correct!")
else:
    print("❌ FAIL: First player advantage calculation is WRONG!")
