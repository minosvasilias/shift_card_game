"""Track Kickback triggers during actual gameplay, not just final state."""

import asyncio
from game.engine import GameEngine
from game.cards import CARD_REGISTRY
from agents.lookahead_agent import LookaheadAgent


class TrackingEngine(GameEngine):
    """Engine that tracks Kickback events during gameplay."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kickback_triggers = 0
        self.kickback_plays = 0
        self.kickback_player = None

    async def _check_center_trigger(self, player_idx: int):
        """Override to track Kickback triggers."""
        player = self.state.players[player_idx]

        if len(player.row) != 3:
            return

        center_card = player.row[1]

        # Track Kickback
        if center_card.card.name == "Kickback" and center_card.face_up:
            self.kickback_triggers += 1
            if self.kickback_player is None:
                self.kickback_player = player_idx

        # Call parent implementation
        await super()._check_center_trigger(player_idx)

    async def _play_card(self, action):
        """Override to track Kickback plays."""
        player = self.state.current
        player_idx = self.state.current_player

        if action.hand_index < len(player.hand):
            card = player.hand[action.hand_index]
            if card.name == "Kickback":
                self.kickback_plays += 1
                if self.kickback_player is None:
                    self.kickback_player = player_idx

        return await super()._play_card(action)


def analyze_kickback_triggers(num_games=100, seed=42):
    """Analyze actual Kickback triggers during gameplay."""
    print("=== KICKBACK TRIGGER ANALYSIS (During Gameplay) ===\n")

    total_plays = 0
    total_triggers = 0
    games_with_kickback = 0
    wins_with_kickback = 0
    total_games = 0

    trigger_distribution = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    max_triggers = 0

    for i in range(num_games):
        agent0 = LookaheadAgent(seed=seed + i, depth=3)
        agent1 = LookaheadAgent(seed=seed + i + 1000000, depth=3)

        engine = TrackingEngine(
            agents=(agent0, agent1),
            seed=seed + i,
            max_turns=10,
        )

        asyncio.run(engine.run_game())
        winner = engine.get_winner()

        if engine.kickback_plays > 0:
            games_with_kickback += 1
            total_plays += engine.kickback_plays
            total_triggers += engine.kickback_triggers

            # Track trigger distribution
            triggers = min(engine.kickback_triggers, 5)
            trigger_distribution[triggers] += 1
            max_triggers = max(max_triggers, engine.kickback_triggers)

            # Track wins
            if winner == engine.kickback_player:
                wins_with_kickback += 1

        total_games += 1

    if games_with_kickback == 0:
        print("No games with Kickback!")
        return

    print(f"Games analyzed: {total_games}")
    print(f"Games with Kickback: {games_with_kickback} ({games_with_kickback/total_games*100:.1f}%)")
    print()

    print("KICKBACK PLAYS:")
    print("-" * 50)
    print(f"Total plays: {total_plays}")
    print(f"Avg plays per game (when played): {total_plays/games_with_kickback:.2f}")
    print()

    print("KICKBACK TRIGGERS:")
    print("-" * 50)
    print(f"Total triggers: {total_triggers}")
    print(f"Avg triggers per game (when played): {total_triggers/games_with_kickback:.2f}")
    print(f"Trigger rate: {total_triggers/total_plays*100:.1f}% of plays trigger")
    print(f"Max triggers in a single game: {max_triggers}")
    print()

    print("TRIGGER DISTRIBUTION:")
    print("-" * 50)
    for triggers in range(max_triggers + 1):
        count = trigger_distribution.get(triggers, 0)
        pct = count / games_with_kickback * 100
        print(f"  {triggers} triggers: {count} games ({pct:.1f}%)")
    print()

    print("WIN RATE:")
    print("-" * 50)
    win_rate = wins_with_kickback / games_with_kickback * 100
    print(f"Win rate when Kickback played: {win_rate:.1f}%")
    print(f"Games won: {wins_with_kickback}/{games_with_kickback}")
    print()


if __name__ == "__main__":
    analyze_kickback_triggers(num_games=200, seed=42)
