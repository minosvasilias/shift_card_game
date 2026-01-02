"""Card definitions and registry for Robot Assembly Line."""

from __future__ import annotations

from .state import Card, CardType, Icon
from . import effects


# =============================================================================
# CARD REGISTRY
# =============================================================================

CARD_REGISTRY: dict[str, Card] = {}


def register_card(card: Card) -> Card:
    """Register a card in the global registry."""
    CARD_REGISTRY[card.name] = card
    return card


# =============================================================================
# CENTER-SCORING CARDS (15 cards)
# =============================================================================

register_card(Card(
    name="Calibration Unit",
    icon=Icon.GEAR,
    card_type=CardType.CENTER,
    effect=effects.effect_calibration_unit,
))

register_card(Card(
    name="Loner Bot",
    icon=Icon.CHIP,
    card_type=CardType.CENTER,
    effect=effects.effect_loner_bot,
))

register_card(Card(
    name="Copycat",
    icon=Icon.GEAR,
    card_type=CardType.CENTER,
    effect=effects.effect_copycat,
))

register_card(Card(
    name="Siphon Drone",
    icon=Icon.SPARK,
    card_type=CardType.CENTER,
    effect=effects.effect_siphon_drone,
))

register_card(Card(
    name="Jealous Unit",
    icon=Icon.HEART,
    card_type=CardType.CENTER,
    effect=effects.effect_jealous_unit,
))

register_card(Card(
    name="Sequence Bot",
    icon=Icon.CHIP,
    card_type=CardType.CENTER,
    effect=effects.effect_sequence_bot,
))

register_card(Card(
    name="Kickback",
    icon=Icon.SPARK,
    card_type=CardType.CENTER,
    effect=effects.effect_kickback,
))

register_card(Card(
    name="Patience Circuit",
    icon=Icon.CHIP,
    card_type=CardType.CENTER,
    effect=effects.effect_patience_circuit,
))

register_card(Card(
    name="Turncoat",
    icon=Icon.HEART,
    card_type=CardType.CENTER,
    effect=effects.effect_turncoat,
))

register_card(Card(
    name="Void",
    icon=None,
    card_type=CardType.CENTER,
    effect=effects.effect_void,
))

register_card(Card(
    name="Buddy System",
    icon=Icon.HEART,
    card_type=CardType.CENTER,
    effect=effects.effect_buddy_system,
))

register_card(Card(
    name="Mimic",
    icon=Icon.CHIP,
    card_type=CardType.CENTER,
    effect=effects.effect_mimic,
))

register_card(Card(
    name="Tug-of-War",
    icon=Icon.GEAR,
    card_type=CardType.CENTER,
    effect=effects.effect_tug_of_war,
))

register_card(Card(
    name="Hollow Frame",
    icon=Icon.GEAR,
    card_type=CardType.CENTER,
    effect=effects.effect_hollow_frame,
))

register_card(Card(
    name="Echo Chamber",
    icon=Icon.CHIP,
    card_type=CardType.CENTER,
    effect=effects.effect_echo_chamber,
))

register_card(Card(
    name="One-Shot",
    icon=Icon.SPARK,
    card_type=CardType.CENTER,
    effect=effects.effect_one_shot,
))

register_card(Card(
    name="Embargo",
    icon=Icon.GEAR,
    card_type=CardType.CENTER,
    effect=effects.effect_embargo,
))

register_card(Card(
    name="Scavenger",
    icon=Icon.GEAR,
    card_type=CardType.CENTER,
    effect=effects.effect_scavenger,
))

register_card(Card(
    name="Magnet",
    icon=Icon.SPARK,
    card_type=CardType.CENTER,
    effect=effects.effect_magnet,
))

register_card(Card(
    name="Hot Potato",
    icon=Icon.SPARK,
    card_type=CardType.CENTER,
    effect=effects.effect_hot_potato,
))


# =============================================================================
# EXIT-SCORING CARDS (6 cards)
# =============================================================================

register_card(Card(
    name="Farewell Unit",
    icon=Icon.HEART,
    card_type=CardType.EXIT,
    effect=effects.effect_farewell_unit,
))

register_card(Card(
    name="Spite Module",
    icon=Icon.CHIP,
    card_type=CardType.EXIT,
    effect=effects.effect_spite_module,
))

register_card(Card(
    name="Boomerang",
    icon=Icon.SPARK,
    card_type=CardType.EXIT,
    effect=effects.effect_boomerang,
))

register_card(Card(
    name="Donation Bot",
    icon=Icon.GEAR,
    card_type=CardType.EXIT,
    effect=effects.effect_donation_bot,
))

register_card(Card(
    name="Rewinder",
    icon=Icon.CHIP,
    card_type=CardType.EXIT,
    effect=effects.effect_rewinder,
))

register_card(Card(
    name="Sacrificial Lamb",
    icon=Icon.HEART,
    card_type=CardType.EXIT,
    effect=effects.effect_sacrificial_lamb,
))


# =============================================================================
# TRAP CARDS (4 cards)
# =============================================================================

register_card(Card(
    name="Tripwire",
    icon=Icon.SPARK,
    card_type=CardType.TRAP,
    effect=effects.effect_tripwire,
    trigger_check=effects.trigger_tripwire,
))

register_card(Card(
    name="False Flag",
    icon=Icon.CHIP,
    card_type=CardType.TRAP,
    effect=effects.effect_false_flag,
    trigger_check=effects.trigger_false_flag,
))

register_card(Card(
    name="Snare",
    icon=Icon.GEAR,
    card_type=CardType.TRAP,
    effect=effects.effect_snare,
    trigger_check=effects.trigger_snare,
))

register_card(Card(
    name="Mirror Trap",
    icon=Icon.HEART,
    card_type=CardType.TRAP,
    effect=effects.effect_mirror_trap,
    trigger_check=effects.trigger_mirror_trap,
))


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_all_cards() -> list[Card]:
    """Get a list of all registered cards."""
    return list(CARD_REGISTRY.values())


def get_cards_by_type(card_type: CardType) -> list[Card]:
    """Get all cards of a specific type."""
    return [c for c in CARD_REGISTRY.values() if c.card_type == card_type]


def get_cards_by_icon(icon: Icon | None) -> list[Card]:
    """Get all cards with a specific icon."""
    return [c for c in CARD_REGISTRY.values() if c.icon == icon]


def create_deck(card_names: list[str] | None = None) -> list[Card]:
    """Create a deck with specified cards or all cards."""
    if card_names is None:
        return get_all_cards()
    return [CARD_REGISTRY[name] for name in card_names]
