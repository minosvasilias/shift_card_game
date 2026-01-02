"""Test what lookahead agents choose when Kickback could trigger."""

from game.state import GameState, PlayerState, CardInPlay, PlayAction, Side
from game.cards import CARD_REGISTRY
from agents.lookahead_agent import LookaheadAgent
from agents.greedy_agent import GreedyAgent


def test_kickback_setup_choice():
    """
    Test: Player has a choice that would make Kickback trigger.
    Do they avoid it?
    """
    print("=== TEST: WOULD AGENTS PUT KICKBACK IN CENTER? ===\n")

    # Scenario: [Calibration, Kickback]
    # Playing to RIGHT will make row=[Calibration, Kickback, NewCard]
    # This puts Kickback in CENTER!

    state = GameState(
        players=[PlayerState(), PlayerState()],
        deck=[CARD_REGISTRY["Calibration Unit"]] * 20,
        market=[CARD_REGISTRY["Farewell Unit"], CARD_REGISTRY["Calibration Unit"], CARD_REGISTRY["Calibration Unit"]],
        turn_counter=1,
        current_player=0,
    )

    # Setup: [Calibration, Kickback] and Farewell in hand
    state.players[0].row = [
        CardInPlay(card=CARD_REGISTRY["Calibration Unit"], face_up=True),
        CardInPlay(card=CARD_REGISTRY["Kickback"], face_up=True),
    ]
    state.players[0].hand = [CARD_REGISTRY["Farewell Unit"]]

    print("Setup:")
    print("  Row: [Calibration Unit, Kickback]")
    print("  Hand: [Farewell Unit]")
    print()
    print("Choices:")
    print("  - Play LEFT: [Farewell, Calibration, Kickback] → Pushes Calibration out, Farewell in center (3 pts)")
    print("  - Play RIGHT: [Calibration, Kickback, Farewell] → Kickback in CENTER! (2 pts + 3 exit = 5 pts)")
    print()

    # Test greedy agent
    print("GREEDY AGENT:")
    greedy = GreedyAgent(seed=42)
    action_greedy = greedy.choose_action(state, 0)
    side_str = "LEFT" if action_greedy.side == Side.LEFT else "RIGHT"
    print(f"  Choice: {side_str}")
    if action_greedy.side == Side.RIGHT:
        print("  → Puts Kickback in center! Triggers for 5 points")
    else:
        print("  → Avoids Kickback trigger, Farewell scores 3")
    print()

    # Test lookahead:2
    print("LOOKAHEAD:2 AGENT:")
    lookahead2 = LookaheadAgent(seed=42, depth=2)
    action_look2 = lookahead2.choose_action(state, 0)
    side_str = "LEFT" if action_look2.side == Side.LEFT else "RIGHT"
    print(f"  Choice: {side_str}")
    if action_look2.side == Side.RIGHT:
        print("  → Puts Kickback in center! Triggers for 5 points")
    else:
        print("  → Avoids Kickback trigger")
    print()

    # Test lookahead:3
    print("LOOKAHEAD:3 AGENT:")
    lookahead3 = LookaheadAgent(seed=42, depth=3)
    action_look3 = lookahead3.choose_action(state, 0)
    side_str = "LEFT" if action_look3.side == Side.LEFT else "RIGHT"
    print(f"  Choice: {side_str}")
    if action_look3.side == Side.RIGHT:
        print("  → Puts Kickback in center! Triggers for 5 points")
    else:
        print("  → Avoids Kickback trigger")
    print()


def test_kickback_vs_better_card():
    """Test if agents prefer playing Kickback or a better card."""
    print("\n=== TEST: KICKBACK VS BETTER CENTER CARD ===\n")

    state = GameState(
        players=[PlayerState(), PlayerState()],
        deck=[CARD_REGISTRY["Calibration Unit"]] * 20,
        market=[CARD_REGISTRY["Calibration Unit"]] * 3,
        turn_counter=1,
        current_player=0,
    )

    # Row has 2 cards, next card goes to center
    state.players[0].row = [
        CardInPlay(card=CARD_REGISTRY["Farewell Unit"], face_up=True),
        CardInPlay(card=CARD_REGISTRY["Farewell Unit"], face_up=True),
    ]

    # Hand has Kickback (2pts) and Jealous Unit (potentially higher)
    state.players[0].hand = [
        CARD_REGISTRY["Kickback"],
        CARD_REGISTRY["Jealous Unit"],
    ]

    # Opponent has some cards with icons
    state.players[1].row = [
        CardInPlay(card=CARD_REGISTRY["Calibration Unit"], face_up=True),
        CardInPlay(card=CARD_REGISTRY["Loner Bot"], face_up=True),
    ]

    print("Setup:")
    print("  Row: [Farewell Unit, Farewell Unit]")
    print("  Hand: [Kickback (2pts), Jealous Unit (4pts with opponent icons)]")
    print("  Next card will be in CENTER")
    print()

    print("LOOKAHEAD:3 CHOICE:")
    agent = LookaheadAgent(seed=42, depth=3)
    action = agent.choose_action(state, 0)

    chosen_card = state.players[0].hand[action.hand_index].name
    print(f"  Plays: {chosen_card}")
    print()

    if chosen_card == "Kickback":
        print("  → Agent chose the weaker card (Kickback)")
    else:
        print("  → Agent chose the stronger card (Jealous Unit)")


if __name__ == "__main__":
    test_kickback_setup_choice()
    test_kickback_vs_better_card()
