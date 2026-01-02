"""Test to verify Embargo duration and Kickback consecutive triggers."""

from game.engine import GameEngine
from game.cards import CARD_REGISTRY
from game.state import PlayAction, Side, DrawChoice
from agents.base import Agent


class TestAgent(Agent):
    """Simple agent for controlled testing."""

    def __init__(self, actions=None):
        self.actions = actions or []
        self.action_index = 0

    def choose_action(self, state, player_idx):
        if self.action_index < len(self.actions):
            action = self.actions[self.action_index]
            self.action_index += 1
            return action
        return PlayAction(hand_index=0, side=Side.RIGHT, face_down=False)

    def choose_draw(self, state, player_idx):
        return DrawChoice.DECK

    def choose_effect_option(self, state, player_idx, choice):
        # For Kickback, always push right
        if choice.choice_type == "kickback_direction":
            return Side.RIGHT
        # Default: choose first option
        return choice.options[0] if choice.options else 0


def test_embargo_duration():
    """Test how many opponent turns Embargo actually locks the market."""
    print("=== TESTING EMBARGO DURATION ===\n")

    # Create a minimal card pool with Embargo and simple cards
    card_pool = [
        CARD_REGISTRY["Embargo"],
        CARD_REGISTRY["Calibration Unit"],
        CARD_REGISTRY["Farewell Unit"],
    ] * 10

    agent0 = TestAgent()
    agent1 = TestAgent()

    engine = GameEngine(
        agents=(agent0, agent1),
        card_pool=card_pool,
        seed=42,
        max_turns=5
    )

    # Manually set up a scenario
    state = engine.state

    # Give Player 0 an Embargo
    state.players[0].hand = [CARD_REGISTRY["Embargo"]]
    state.players[1].hand = [CARD_REGISTRY["Calibration Unit"], CARD_REGISTRY["Calibration Unit"]]

    # Fill market
    state.market = [CARD_REGISTRY["Calibration Unit"]] * 3

    print(f"Initial turn_counter: {state.turn_counter}")
    print(f"Player 0 hand: {[c.name for c in state.players[0].hand]}")
    print(f"Market available: {len(state.market)} cards\n")

    # Player 0 plays Embargo
    print("--- Player 0's Turn (Round 1) ---")
    action = PlayAction(hand_index=0, side=Side.RIGHT, face_down=False)
    state.players[0].hand = [CARD_REGISTRY["Embargo"]]

    # Simulate the turn manually to track embargo
    from game.state import CardInPlay
    embargo_card = CardInPlay(card=CARD_REGISTRY["Embargo"], face_up=True)
    state.players[0].row.append(embargo_card)

    # Trigger effect
    points = CARD_REGISTRY["Embargo"].effect(state, embargo_card, 0, agent0)
    state.players[0].score += points

    print(f"Embargo played! Score: {points}")
    print(f"Turn counter: {state.turn_counter}")

    # Check active effects
    embargo_effect = [e for e in state.active_effects if e.effect_type == "embargo"][0]
    print(f"Embargo expires_turn: {embargo_effect.expires_turn}")
    print(f"Active effects: {len(state.active_effects)}\n")

    # Now check each subsequent turn
    for round_num in range(1, 4):
        for player_idx in [1, 0]:  # Player 1, then Player 0
            turn_name = f"Round {round_num} - Player {player_idx}"
            print(f"--- {turn_name} ---")
            print(f"Turn counter: {state.turn_counter}")

            has_embargo = state.has_embargo(player_idx)
            print(f"Player {player_idx} has embargo: {has_embargo}")

            is_active = embargo_effect.expires_turn > state.turn_counter
            print(f"Effect active: {is_active} (expires_turn {embargo_effect.expires_turn} > turn_counter {state.turn_counter})")

            if player_idx == 1 and has_embargo:
                print(f"⚠️  MARKET LOCKED FOR PLAYER 1")

            print()

            # Increment turn counter as engine does
            if player_idx == 1:
                state.turn_counter += 1

    print("\n=== EMBARGO CONCLUSION ===")
    print("Expected: Embargo locks market for ONE opponent turn")
    print("Actual: Check the output above - does it lock for round 1 only, or rounds 1 AND 2?")
    print()


def test_kickback_consecutive():
    """Test if Kickback can trigger on consecutive turns."""
    print("=== TESTING KICKBACK CONSECUTIVE TRIGGERS ===\n")

    card_pool = [
        CARD_REGISTRY["Kickback"],
        CARD_REGISTRY["Farewell Unit"],
        CARD_REGISTRY["Calibration Unit"],
    ] * 10

    agent = TestAgent()

    from game.state import GameState, PlayerState, CardInPlay
    state = GameState(
        players=[PlayerState(), PlayerState()],
        deck=card_pool[:],
        market=[],
        turn_counter=1,
        current_player=0,
    )

    # Set up: Player has [Calibration, Kickback, Farewell]
    player = state.players[0]
    player.row = [
        CardInPlay(card=CARD_REGISTRY["Calibration Unit"], face_up=True),
        CardInPlay(card=CARD_REGISTRY["Kickback"], face_up=True),
        CardInPlay(card=CARD_REGISTRY["Farewell Unit"], face_up=True),
    ]

    print("Initial row: [Calibration Unit, Kickback, Farewell Unit]")
    print(f"Row length: {len(player.row)}")
    print()

    # Turn 1: Kickback is center, should trigger
    print("--- Turn 1 ---")
    print("Kickback is in center position (index 1)")
    print(f"Is center card: {player.row[1].name}")

    # Manually trigger center effect
    kickback_card = player.row[1]
    points = kickback_card.card.effect(state, kickback_card, 0, agent)
    print(f"Kickback triggers! Scores: {points}")

    # Handle the push
    if "kickback_pushed_card" in kickback_card.metadata:
        pushed = kickback_card.metadata.pop("kickback_pushed_card")
        print(f"Kickback pushes out: {pushed.name}")

        # Trigger exit effect
        if pushed.card.card_type.name == "EXIT":
            exit_points = pushed.card.effect(state, pushed, 0, agent)
            print(f"Exit effect triggers! Scores: {exit_points}")

        player.row.remove(pushed)

    print(f"Row after trigger: {[c.name for c in player.row]}")
    print(f"Row length: {len(player.row)}")
    print()

    # Turn 2: Add another Farewell Unit
    print("--- Turn 2 ---")
    print("Adding new Farewell Unit to right side...")
    new_farewell = CardInPlay(card=CARD_REGISTRY["Farewell Unit"], face_up=True)
    player.row.append(new_farewell)

    print(f"Row after adding: {[c.name for c in player.row]}")
    print(f"Row length: {len(player.row)}")
    print(f"Center card (index 1): {player.row[1].name if len(player.row) > 1 else 'None'}")

    if len(player.row) == 3:
        print("\n✓ Row has 3 cards - center trigger should fire!")
        print(f"Center position is: {player.row[1].name}")

        if player.row[1] == kickback_card:
            print("✓ Kickback is STILL the center card!")
            print("✓ Kickback CAN trigger again on consecutive turns!")

            # Trigger again
            points2 = kickback_card.card.effect(state, kickback_card, 0, agent)
            print(f"\nKickback triggers AGAIN! Scores: {points2}")

            if "kickback_pushed_card" in kickback_card.metadata:
                pushed2 = kickback_card.metadata.pop("kickback_pushed_card")
                print(f"Pushes out: {pushed2.name}")
                exit_points2 = pushed2.card.effect(state, pushed2, 0, agent)
                print(f"Exit effect triggers! Scores: {exit_points2}")

    print("\n=== KICKBACK CONCLUSION ===")
    print("Kickback CAN trigger on consecutive turns by:")
    print("1. [A, Kickback, Exit] → trigger → [A, Kickback]")
    print("2. Add Exit → [A, Kickback, Exit] → trigger again!")
    print("This allows multiple exit triggers and is extremely powerful!")
    print()


if __name__ == "__main__":
    test_embargo_duration()
    print("\n" + "="*60 + "\n")
    test_kickback_consecutive()
