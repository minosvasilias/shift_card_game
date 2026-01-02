"""Deep analysis: WHY isn't Kickback triggering?"""

from game.engine import GameEngine
from game.cards import CARD_REGISTRY
from agents.lookahead_agent import LookaheadAgent


def analyze_single_kickback_game(seed, verbose=True):
    """Track ONE game in detail to see what happens to Kickback."""
    agent0 = LookaheadAgent(seed=seed, depth=3)
    agent1 = LookaheadAgent(seed=seed + 1000000, depth=3)

    engine = GameEngine(
        agents=(agent0, agent1),
        seed=seed,
        max_turns=10,
    )

    print(f"=== GAME WITH SEED {seed} ===\n")

    # Track Kickback through the game
    kickback_events = []
    kickback_player = None

    turn = 0
    while not engine.state.game_over and turn < 20:
        state = engine.state
        player_idx = state.current_player
        player = state.players[player_idx]

        # Check for Kickback in hand
        for card in player.hand:
            if card.name == "Kickback":
                if kickback_player is None:
                    kickback_player = player_idx
                    kickback_events.append(f"Turn {turn}: Player {player_idx} has Kickback in hand")

        # Check for Kickback in row
        for idx, card_in_play in enumerate(player.row):
            if card_in_play.name == "Kickback":
                if kickback_player is None:
                    kickback_player = player_idx

                face = "FACE-UP" if card_in_play.face_up else "FACE-DOWN"
                position_str = ["LEFT", "CENTER", "RIGHT"][idx] if len(player.row) == 3 else f"pos{idx}"
                row_len = len(player.row)

                event = f"Turn {turn}: Player {player_idx} - Kickback in row at {position_str} ({face}), row length={row_len}"

                # Check if it COULD trigger
                if idx == 1 and row_len == 3 and card_in_play.face_up:
                    event += " ← COULD TRIGGER!"

                kickback_events.append(event)

        # Check for Kickback in market
        for card in state.market:
            if card.name == "Kickback":
                kickback_events.append(f"Turn {turn}: Kickback in market")

        # Play turn
        engine.play_turn()
        turn += 1

    # Print events
    if kickback_events:
        print("KICKBACK TIMELINE:")
        print("-" * 60)
        for event in kickback_events:
            print(f"  {event}")
        print()

        # Check final state
        winner = engine.get_winner()
        if kickback_player is not None:
            won_str = "WON" if winner == kickback_player else "LOST"
            print(f"Result: Player {kickback_player} (Kickback holder) {won_str}")
            print(f"Scores: P0={engine.state.players[0].score}, P1={engine.state.players[1].score}")
        print()
    else:
        print("Kickback did not appear in this game.\n")

    return len(kickback_events) > 0


def find_kickback_games(max_games=50):
    """Find games where Kickback appears and analyze them."""
    print("=== SEARCHING FOR KICKBACK GAMES ===\n")

    games_analyzed = 0
    games_found = 0

    for seed in range(42, 42 + max_games):
        if games_found >= 5:  # Analyze first 5 games with Kickback
            break

        # Quick check if Kickback appears
        agent0 = LookaheadAgent(seed=seed, depth=3)
        agent1 = LookaheadAgent(seed=seed + 1000000, depth=3)
        engine = GameEngine(agents=(agent0, agent1), seed=seed, max_turns=10)
        final_state = engine.run_game()

        has_kickback = False
        for player in final_state.players:
            for card in player.row:
                if card.name == "Kickback":
                    has_kickback = True
                    break

        if has_kickback:
            games_found += 1
            analyze_single_kickback_game(seed, verbose=True)

        games_analyzed += 1

    print(f"\nAnalyzed {games_analyzed} games, found {games_found} with Kickback in final row")
    print()


def analyze_lookahead_heuristic():
    """Check how lookahead agents evaluate Kickback."""
    print("=== LOOKAHEAD AGENT EVALUATION ===\n")

    from game.state import GameState, PlayerState, CardInPlay, Side

    # Create a test state
    state = GameState(
        players=[PlayerState(), PlayerState()],
        deck=CARD_REGISTRY["Calibration Unit"],
        market=[CARD_REGISTRY["Farewell Unit"]] * 3,
        turn_counter=1,
        current_player=0,
    )

    # Give player Kickback and an exit card in hand
    state.players[0].hand = [
        CARD_REGISTRY["Kickback"],
        CARD_REGISTRY["Farewell Unit"],
    ]

    # Set up row: [Calibration, empty, empty]
    state.players[0].row = [
        CardInPlay(card=CARD_REGISTRY["Calibration Unit"], face_up=True)
    ]

    print("Test scenario:")
    print("  Hand: [Kickback, Farewell Unit]")
    print("  Row: [Calibration Unit]")
    print("  Market: [Farewell Unit, Farewell Unit, Farewell Unit]")
    print()

    agent = LookaheadAgent(seed=42, depth=3)

    print("What would lookahead:3 do?")
    print("-" * 60)

    # Get agent's action
    action = agent.choose_action(state, 0)

    card_played = state.players[0].hand[action.hand_index].name
    side_str = "LEFT" if action.side == Side.LEFT else "RIGHT"
    face_str = "FACE-DOWN" if action.face_down else "FACE-UP"

    print(f"Agent plays: {card_played} to {side_str} ({face_str})")
    print()

    # Try again with Kickback in a better position
    state2 = GameState(
        players=[PlayerState(), PlayerState()],
        deck=[CARD_REGISTRY["Calibration Unit"]] * 20,
        market=[CARD_REGISTRY["Farewell Unit"]] * 3,
        turn_counter=1,
        current_player=0,
    )

    # Give player setup where Kickback WOULD trigger
    state2.players[0].hand = [
        CARD_REGISTRY["Farewell Unit"],
    ]

    state2.players[0].row = [
        CardInPlay(card=CARD_REGISTRY["Calibration Unit"], face_up=True),
        CardInPlay(card=CARD_REGISTRY["Kickback"], face_up=True),
    ]

    print("Test scenario 2 (Kickback already in row):")
    print("  Hand: [Farewell Unit]")
    print("  Row: [Calibration Unit, Kickback]")
    print("  Next card will make Kickback trigger!")
    print()

    action2 = agent.choose_action(state2, 0)
    side_str2 = "LEFT" if action2.side == Side.LEFT else "RIGHT"

    print(f"Agent plays Farewell Unit to {side_str2}")

    if action2.side == Side.RIGHT:
        print("  → This puts Kickback in CENTER! It will trigger!")
    else:
        print("  → This avoids putting Kickback in center")
    print()


if __name__ == "__main__":
    find_kickback_games(max_games=100)
    print("\n" + "=" * 60 + "\n")
    analyze_lookahead_heuristic()
