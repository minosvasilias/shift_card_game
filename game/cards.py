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
    effect_text="Score 2 points.",
    effect=effects.effect_calibration_unit,
))

register_card(Card(
    name="Loner Bot",
    icon=Icon.CHIP,
    card_type=CardType.CENTER,
    effect_text="Score 4 if no adjacent card shares your icon. Otherwise 0.",
    effect=effects.effect_loner_bot,
))

register_card(Card(
    name="Siphon Drone",
    icon=Icon.SPARK,
    card_type=CardType.CENTER,
    effect_text="Score 3 points. Opponent also scores 2.",
    effect=effects.effect_siphon_drone,
))

register_card(Card(
    name="Jealous Unit",
    icon=Icon.HEART,
    card_type=CardType.CENTER,
    effect_text="Score 2 per opponent's card that shares your icon.",
    effect=effects.effect_jealous_unit,
))

register_card(Card(
    name="Sequence Bot",
    icon=Icon.CHIP,
    card_type=CardType.CENTER,
    effect_text="Score 3 if your row has exactly three different icons. Otherwise 1.",
    effect=effects.effect_sequence_bot,
))

register_card(Card(
    name="Kickback",
    icon=Icon.SPARK,
    card_type=CardType.CENTER,
    effect_text="Score 2. Push this card one slot toward either edge (your choice).",
    effect=effects.effect_kickback,
))

register_card(Card(
    name="Patience Circuit",
    icon=Icon.CHIP,
    card_type=CardType.CENTER,
    effect_text="At game end, score 1 per turn this card was in center.",
    effect=effects.effect_patience_circuit,
))

register_card(Card(
    name="Turncoat",
    icon=Icon.HEART,
    card_type=CardType.CENTER,
    effect_text="Score 2. Swap this card with one in opponent's row.",
    effect=effects.effect_turncoat,
))

register_card(Card(
    name="Void",
    icon=None,
    card_type=CardType.CENTER,
    effect_text="Score 2 per empty slot across both rows.",
    effect=effects.effect_void,
))

register_card(Card(
    name="Mimic",
    icon=Icon.CHIP,
    card_type=CardType.CENTER,
    effect_text="This card's icon becomes the icon of the card to its left. Score 2.",
    effect=effects.effect_mimic,
))

register_card(Card(
    name="Tug-of-War",
    icon=Icon.GEAR,
    card_type=CardType.CENTER,
    effect_text="Score 1. Opponent must push out an edge card if they have 3.",
    effect=effects.effect_tug_of_war,
))

register_card(Card(
    name="Hollow Frame",
    icon=Icon.GEAR,
    card_type=CardType.CENTER,
    effect_text="Score 0. This card counts as having every icon for adjacency.",
    effect=effects.effect_hollow_frame,
))

register_card(Card(
    name="Echo Chamber",
    icon=Icon.CHIP,
    card_type=CardType.CENTER,
    effect_text="Score 4 if turn counter is even. Otherwise 0.",
    effect=effects.effect_echo_chamber,
))

register_card(Card(
    name="One-Shot",
    icon=Icon.SPARK,
    card_type=CardType.CENTER,
    effect_text="Score 5. Remove this card from the game entirely.",
    effect=effects.effect_one_shot,
))

register_card(Card(
    name="Embargo",
    icon=Icon.GEAR,
    card_type=CardType.CENTER,
    effect_text="Score 1. Market is locked for opponent until your next turn.",
    effect=effects.effect_embargo,
))

register_card(Card(
    name="Scavenger",
    icon=Icon.GEAR,
    card_type=CardType.CENTER,
    effect_text="Score 0. Look at all face-down cards. May swap this with one.",
    effect=effects.effect_scavenger,
))

register_card(Card(
    name="Magnet",
    icon=Icon.SPARK,
    card_type=CardType.CENTER,
    effect_text="Score 1. Pull one card from market into an adjacent slot.",
    effect=effects.effect_magnet,
))

register_card(Card(
    name="Hot Potato",
    icon=Icon.SPARK,
    card_type=CardType.CENTER,
    effect_text="Score 2. This card goes to opponent's hand.",
    effect=effects.effect_hot_potato,
))

register_card(Card(
    name="Parasite",
    icon=Icon.CHIP,
    card_type=CardType.CENTER,
    effect_text="Score 4. Swap positions with a card in opponent's row.",
    effect=effects.effect_parasite,
))

register_card(Card(
    name="Auctioneer",
    icon=Icon.HEART,
    card_type=CardType.CENTER,
    effect_text="Score 2 per icon type in your hand that opponent lacks.",
    effect=effects.effect_auctioneer,
))

register_card(Card(
    name="Chain Reaction",
    icon=Icon.SPARK,
    card_type=CardType.CENTER,
    effect_text="Score 2. Then trigger the center effect of the card to your left.",
    effect=effects.effect_chain_reaction,
))

register_card(Card(
    name="Time Bomb",
    icon=Icon.CHIP,
    card_type=CardType.CENTER,
    effect_text="First trigger: store turn. Later: score turns elapsed since last trigger.",
    effect=effects.effect_time_bomb,
))

register_card(Card(
    name="Compressor",
    icon=Icon.SPARK,
    card_type=CardType.CENTER,
    effect_text="Score 5. Push both edge cards out of your row.",
    effect=effects.effect_compressor,
))

register_card(Card(
    name="Extraction",
    icon=Icon.GEAR,
    card_type=CardType.CENTER,
    effect_text="Score 1. Take a card from opponent's row and add it to your hand.",
    effect=effects.effect_extraction,
))

register_card(Card(
    name="Purge",
    icon=Icon.CHIP,
    card_type=CardType.CENTER,
    effect_text="Score 1. Choose a card in opponent's row and trash it permanently.",
    effect=effects.effect_purge,
))

register_card(Card(
    name="Sniper",
    icon=Icon.GEAR,
    card_type=CardType.CENTER,
    effect_text="Score 2. Choose any card in opponent's row and push it out.",
    effect=effects.effect_sniper,
))


# =============================================================================
# EXIT-SCORING CARDS (6 cards)
# =============================================================================

register_card(Card(
    name="Farewell Unit",
    icon=Icon.HEART,
    card_type=CardType.EXIT,
    effect_text="Score 3 when pushed out.",
    effect=effects.effect_farewell_unit,
))

register_card(Card(
    name="Spite Module",
    icon=Icon.CHIP,
    card_type=CardType.EXIT,
    effect_text="Opponent must push out one of their edge cards (no score).",
    effect=effects.effect_spite_module,
))

register_card(Card(
    name="Boomerang",
    icon=Icon.SPARK,
    card_type=CardType.EXIT,
    effect_text="Return to your hand. Cannot play this next turn.",
    effect=effects.effect_boomerang,
))

register_card(Card(
    name="Donation Bot",
    icon=Icon.GEAR,
    card_type=CardType.EXIT,
    effect_text="Goes to opponent's hand instead of market.",
    effect=effects.effect_donation_bot,
))

register_card(Card(
    name="Rewinder",
    icon=Icon.CHIP,
    card_type=CardType.EXIT,
    effect_text="Take one card from market into your hand.",
    effect=effects.effect_rewinder,
))

register_card(Card(
    name="Sacrificial Lamb",
    icon=Icon.HEART,
    card_type=CardType.EXIT,
    effect_text="Score 3 when pushed out (no center effect).",
    effect=effects.effect_sacrificial_lamb,
))

register_card(Card(
    name="Phoenix",
    icon=Icon.SPARK,
    card_type=CardType.EXIT,
    effect_text="Go to top of deck instead of market. Score 2.",
    effect=effects.effect_phoenix,
))

register_card(Card(
    name="Sabotage",
    icon=Icon.GEAR,
    card_type=CardType.EXIT,
    effect_text="Opponent must trash an edge card from their row.",
    effect=effects.effect_sabotage,
))

register_card(Card(
    name="Roadblock",
    icon=Icon.HEART,
    card_type=CardType.EXIT,
    effect_text="Opponent cannot play to this side next turn.",
    effect=effects.effect_roadblock,
))

register_card(Card(
    name="Recruiter",
    icon=Icon.CHIP,
    card_type=CardType.EXIT,
    effect_text="Search deck for any card, add to hand, shuffle deck.",
    effect=effects.effect_recruiter,
))


# =============================================================================
# TRAP CARDS (4 cards)
# =============================================================================

register_card(Card(
    name="Tripwire",
    icon=Icon.SPARK,
    card_type=CardType.TRAP,
    effect_text="TRAP: When opponent scores from center, cancel it. You score 1.",
    effect=effects.effect_tripwire,
    trigger_check=effects.trigger_tripwire,
))

register_card(Card(
    name="False Flag",
    icon=Icon.CHIP,
    card_type=CardType.TRAP,
    effect_text="TRAP: When opponent takes from market, redirect it to your hand.",
    effect=effects.effect_false_flag,
    trigger_check=effects.trigger_false_flag,
))

register_card(Card(
    name="Snare",
    icon=Icon.GEAR,
    card_type=CardType.TRAP,
    effect_text="TRAP: When opponent plays card matching your center icon, send to market.",
    effect=effects.effect_snare,
    trigger_check=effects.trigger_snare,
))

register_card(Card(
    name="Mirror Trap",
    icon=Icon.HEART,
    card_type=CardType.TRAP,
    effect_text="TRAP: When opponent's center card scores, you score the same amount.",
    effect=effects.effect_mirror_trap,
    trigger_check=effects.trigger_mirror_trap,
))

register_card(Card(
    name="Ambush",
    icon=Icon.GEAR,
    card_type=CardType.TRAP,
    effect_text="TRAP: When opponent plays to same side, steal that card to your hand.",
    effect=effects.effect_ambush,
    trigger_check=effects.trigger_ambush,
))

register_card(Card(
    name="Tax Collector",
    icon=Icon.CHIP,
    card_type=CardType.TRAP,
    effect_text="TRAP: When opponent scores 4+ points in one turn, nullify it.",
    effect=effects.effect_tax_collector,
    trigger_check=effects.trigger_tax_collector,
))

register_card(Card(
    name="Mirror Match",
    icon=Icon.HEART,
    card_type=CardType.TRAP,
    effect_text="TRAP: When opponent plays card with same icon, nullify it. Score 1.",
    effect=effects.effect_mirror_match,
    trigger_check=effects.trigger_mirror_match,
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
