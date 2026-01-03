"""Test the new opponent control cards: Extraction, Purge, and Sniper."""

from game.engine import GameEngine
from game.cards import CARD_REGISTRY
from game.state import PlayAction, Side, DrawChoice, CardInPlay
from agents.base import Agent


class TestAgent(Agent):
    """Simple agent for controlled testing."""

    def __init__(self, effect_choices=None):
        self.effect_choices = effect_choices or {}

    def choose_action(self, state, player_idx):
        return PlayAction(hand_index=0, side=Side.RIGHT, face_down=False)

    def choose_draw(self, state, player_idx):
        return DrawChoice.DECK

    def choose_effect_option(self, state, player_idx, choice):
        # Return predefined choice or default to first option
        return self.effect_choices.get(choice.choice_type, choice.options[0])


def test_extraction():
    """Test that Extraction takes a card from opponent's row to your hand."""
    print("=== TESTING EXTRACTION ===\n")

    state_mock = type('obj', (object,), {
        'players': [
            type('obj', (object,), {'row': [], 'hand': [], 'score': 0})(),
            type('obj', (object,), {'row': [], 'hand': [], 'score': 0})()
        ],
        'turn_counter': 1
    })()

    # Setup: Player 1 has 2 cards in row
    calibration = CardInPlay(card=CARD_REGISTRY["Calibration Unit"], face_up=True)
    farewell = CardInPlay(card=CARD_REGISTRY["Farewell Unit"], face_up=True)
    state_mock.players[1].row = [calibration, farewell]

    # Player 0 uses Extraction
    extraction_card = CardInPlay(card=CARD_REGISTRY["Extraction"], face_up=True)

    # Agent chooses to extract the first card (index 0)
    agent = TestAgent(effect_choices={"extraction_target": 0})

    print(f"Before: Opponent row has {len(state_mock.players[1].row)} cards")
    print(f"Before: Player hand has {len(state_mock.players[0].hand)} cards")

    score = CARD_REGISTRY["Extraction"].effect(state_mock, extraction_card, 0, agent)

    print(f"After: Opponent row has {len(state_mock.players[1].row)} cards")
    print(f"After: Player hand has {len(state_mock.players[0].hand)} cards")
    print(f"Score: {score}")

    assert len(state_mock.players[1].row) == 1, "Opponent should have 1 card left"
    assert len(state_mock.players[0].hand) == 1, "Player should have 1 card in hand"
    assert state_mock.players[0].hand[0].name == "Calibration Unit", "Extracted card should be Calibration Unit"
    assert score == 1, "Should score 1 point"

    print("✓ Extraction test passed!\n")


def test_purge():
    """Test that Purge permanently removes a card from opponent's row."""
    print("=== TESTING PURGE ===\n")

    state_mock = type('obj', (object,), {
        'players': [
            type('obj', (object,), {'row': [], 'hand': [], 'score': 0})(),
            type('obj', (object,), {'row': [], 'hand': [], 'score': 0})()
        ],
        'turn_counter': 1
    })()

    # Setup: Player 1 has 3 cards in row
    card1 = CardInPlay(card=CARD_REGISTRY["Calibration Unit"], face_up=True)
    card2 = CardInPlay(card=CARD_REGISTRY["Farewell Unit"], face_up=True)
    card3 = CardInPlay(card=CARD_REGISTRY["Loner Bot"], face_up=True)
    state_mock.players[1].row = [card1, card2, card3]

    # Player 0 uses Purge
    purge_card = CardInPlay(card=CARD_REGISTRY["Purge"], face_up=True)

    # Agent chooses to purge the middle card (index 1)
    agent = TestAgent(effect_choices={"purge_target": 1})

    print(f"Before: Opponent row has {len(state_mock.players[1].row)} cards")

    score = CARD_REGISTRY["Purge"].effect(state_mock, purge_card, 0, agent)

    print(f"After: Opponent row has {len(state_mock.players[1].row)} cards")
    print(f"Score: {score}")

    assert len(state_mock.players[1].row) == 2, "Opponent should have 2 cards left"
    assert state_mock.players[1].row[0].name == "Calibration Unit", "First card should remain"
    assert state_mock.players[1].row[1].name == "Loner Bot", "Third card should remain"
    assert score == 1, "Should score 1 point"

    print("✓ Purge test passed!\n")


def test_sniper():
    """Test that Sniper marks a card to be pushed out with exit effect."""
    print("=== TESTING SNIPER ===\n")

    state_mock = type('obj', (object,), {
        'players': [
            type('obj', (object,), {'row': [], 'hand': [], 'score': 0})(),
            type('obj', (object,), {'row': [], 'hand': [], 'score': 0})()
        ],
        'turn_counter': 1
    })()

    # Setup: Player 1 has 3 cards in row
    card1 = CardInPlay(card=CARD_REGISTRY["Calibration Unit"], face_up=True)
    card2 = CardInPlay(card=CARD_REGISTRY["Farewell Unit"], face_up=True)
    card3 = CardInPlay(card=CARD_REGISTRY["Loner Bot"], face_up=True)
    state_mock.players[1].row = [card1, card2, card3]

    # Player 0 uses Sniper
    sniper_card = CardInPlay(card=CARD_REGISTRY["Sniper"], face_up=True)

    # Agent chooses to snipe the center card (index 1)
    agent = TestAgent(effect_choices={"sniper_target": 1})

    print(f"Before: Opponent row has {len(state_mock.players[1].row)} cards")

    score = CARD_REGISTRY["Sniper"].effect(state_mock, sniper_card, 0, agent)

    print(f"After effect: Opponent row still has {len(state_mock.players[1].row)} cards (engine will handle removal)")
    print(f"Sniper metadata set: {sniper_card.metadata.get('sniper_target') is not None}")
    print(f"Target card: {sniper_card.metadata.get('sniper_target').name if sniper_card.metadata.get('sniper_target') else 'None'}")
    print(f"Score: {score}")

    # The card isn't removed yet - engine handles it
    assert sniper_card.metadata.get("sniper_target") == card2, "Should mark Farewell Unit for pushing"
    assert sniper_card.metadata.get("sniper_target_idx") == 1, "Should store target index"
    assert sniper_card.metadata.get("sniper_opponent_idx") == 1, "Should store opponent index"
    assert score == 2, "Should score 2 points"

    print("✓ Sniper test passed!\n")


if __name__ == "__main__":
    test_extraction()
    test_purge()
    test_sniper()
    print("=== ALL TESTS PASSED ===")
