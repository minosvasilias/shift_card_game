"""Core game state dataclasses and enums."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Any


class Icon(Enum):
    """Card icon types for adjacency conditions."""
    GEAR = auto()
    SPARK = auto()
    CHIP = auto()
    HEART = auto()


class CardType(Enum):
    """Card effect trigger type."""
    CENTER = auto()  # Triggers when card enters center position
    EXIT = auto()    # Triggers when card is pushed out
    TRAP = auto()    # Triggers on specific game events


class Side(Enum):
    """Which side of the row to play/push from."""
    LEFT = auto()
    RIGHT = auto()


class DrawChoice(Enum):
    """Where to draw a card from."""
    DECK = auto()
    MARKET = auto()


class EventType(Enum):
    """Game events that can trigger traps."""
    CARD_SCORED = auto()        # A center effect scored points
    CARD_DRAWN_MARKET = auto()  # A card was taken from market
    CARD_PLAYED = auto()        # A card was played to a row


@dataclass
class Event:
    """A game event that may trigger traps."""
    event_type: EventType
    player_idx: int  # Player who caused the event
    card_name: str | None = None
    icon: Icon | None = None
    points: int = 0


@dataclass
class Card:
    """A card definition (template, not an instance in play)."""
    name: str
    icon: Icon | None
    card_type: CardType
    # Effect function signature: (game_state, card_in_play, player_idx, agent) -> points scored
    # Agent is passed for effects requiring player choices
    effect: Callable[..., int] = field(default=lambda *args: 0)
    # Trap trigger check: (event, game_state, card_in_play, player_idx) -> should trigger
    trigger_check: Callable[..., bool] | None = None

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return False
        return self.name == other.name


@dataclass
class CardInPlay:
    """A card instance in a player's row."""
    card: Card
    face_up: bool = True
    # For tracking effects like Patience Circuit
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.card.name

    @property
    def icon(self) -> Icon | None:
        # Face-down cards don't expose their icon
        return self.card.icon if self.face_up else None

    @property
    def effective_icons(self) -> set[Icon]:
        """Get all icons this card counts as (for Hollow Frame)."""
        if not self.face_up:
            return set()
        if self.metadata.get("all_icons"):
            return set(Icon)
        if self.card.icon is None:
            return set()
        return {self.card.icon}


@dataclass
class PlayAction:
    """An action to play a card from hand."""
    hand_index: int
    side: Side
    face_down: bool = False  # For trap cards


@dataclass
class EffectChoice:
    """A choice the agent needs to make during effect resolution."""
    choice_type: str
    options: list[Any]
    description: str


@dataclass
class ActiveEffect:
    """A persistent effect active in the game."""
    effect_type: str
    player_idx: int
    data: dict[str, Any] = field(default_factory=dict)
    expires_turn: int | None = None


@dataclass
class PlayerState:
    """State for one player."""
    hand: list[Card] = field(default_factory=list)
    row: list[CardInPlay] = field(default_factory=list)
    score: int = 0

    def copy(self) -> PlayerState:
        """Create a deep copy of this player state."""
        return PlayerState(
            hand=list(self.hand),
            row=[CardInPlay(
                card=c.card,
                face_up=c.face_up,
                metadata=dict(c.metadata)
            ) for c in self.row],
            score=self.score
        )


@dataclass
class GameState:
    """Complete game state."""
    players: list[PlayerState] = field(default_factory=lambda: [PlayerState(), PlayerState()])
    market: list[Card] = field(default_factory=list)
    deck: list[Card] = field(default_factory=list)
    turn_counter: int = 1
    current_player: int = 0
    active_effects: list[ActiveEffect] = field(default_factory=list)
    game_over: bool = False
    # For tracking what happened this turn (useful for analytics)
    turn_events: list[Event] = field(default_factory=list)
    # Players who need immediate hand limit enforcement (set by effects like Hot Potato)
    # Maps player_idx -> card name that cannot be discarded (the card just received)
    pending_hand_limit_checks: dict[int, str] = field(default_factory=dict)

    @property
    def current(self) -> PlayerState:
        """Get the current player's state."""
        return self.players[self.current_player]

    @property
    def opponent(self) -> PlayerState:
        """Get the opponent's state."""
        return self.players[1 - self.current_player]

    @property
    def opponent_idx(self) -> int:
        """Get the opponent's index."""
        return 1 - self.current_player

    def copy(self) -> GameState:
        """Create a deep copy of this game state."""
        return GameState(
            players=[p.copy() for p in self.players],
            market=list(self.market),
            deck=list(self.deck),
            turn_counter=self.turn_counter,
            current_player=self.current_player,
            active_effects=[ActiveEffect(
                effect_type=e.effect_type,
                player_idx=e.player_idx,
                data=dict(e.data),
                expires_turn=e.expires_turn
            ) for e in self.active_effects],
            game_over=self.game_over,
            turn_events=list(self.turn_events),
            pending_hand_limit_checks=dict(self.pending_hand_limit_checks),
        )

    def get_center_card(self, player_idx: int) -> CardInPlay | None:
        """Get the center card for a player (only exists with 3 cards)."""
        row = self.players[player_idx].row
        if len(row) == 3:
            return row[1]
        return None

    def get_adjacent_cards(self, player_idx: int, position: int) -> tuple[CardInPlay | None, CardInPlay | None]:
        """Get cards adjacent to a position (left, right)."""
        row = self.players[player_idx].row
        left = row[position - 1] if position > 0 else None
        right = row[position + 1] if position < len(row) - 1 else None
        return left, right

    def has_embargo(self, player_idx: int) -> bool:
        """Check if market is locked for a player."""
        return any(
            e.effect_type == "embargo" and
            e.player_idx != player_idx and
            (e.expires_turn is None or e.expires_turn > self.turn_counter)
            for e in self.active_effects
        )
