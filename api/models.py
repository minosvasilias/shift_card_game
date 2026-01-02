"""
Pydantic models for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Literal


class NewGameRequest(BaseModel):
    """Request to create a new game."""
    opponent: Literal['random', 'greedy', 'lookahead'] = Field(
        default='greedy',
        description="Type of AI opponent"
    )
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility"
    )
    max_turns: int = Field(
        default=10,
        description="Maximum number of turns before game ends"
    )


class PlayActionRequest(BaseModel):
    """Request to play a card."""
    hand_index: int = Field(description="Index of card in hand (0-2)")
    side: Literal['LEFT', 'RIGHT'] = Field(description="Which side to place the card")
    face_down: bool = Field(default=False, description="Whether to play face-down")


class DrawChoiceRequest(BaseModel):
    """Request to choose where to draw from."""
    source: Literal['DECK', 'MARKET'] = Field(description="Draw from deck or market")
    market_index: int | None = Field(
        default=None,
        description="If drawing from market, which card (0-2)"
    )


class EffectChoiceRequest(BaseModel):
    """Request to make an effect choice."""
    choice: int | str | bool = Field(
        description="The choice value (type depends on effect)"
    )


class CardInfo(BaseModel):
    """Information about a card."""
    name: str
    icon: str
    type: str
    description: str


class CardInPlayInfo(BaseModel):
    """Information about a card in play."""
    card: CardInfo
    face_down: bool


class PlayerStateInfo(BaseModel):
    """Information about a player's state."""
    hand: list[CardInfo]
    row: list[CardInPlayInfo]
    score: int


class GameStateResponse(BaseModel):
    """Response containing current game state."""
    game_id: str
    current_turn: int
    current_player: int
    players: list[PlayerStateInfo]
    market: list[CardInfo]
    deck_size: int
    is_game_over: bool
    winner: int | None
    waiting_for: str | None  # 'action', 'draw', 'effect', or None
    effect_choice_type: str | None  # Details about what effect choice is needed


class GameCreatedResponse(BaseModel):
    """Response after creating a new game."""
    game_id: str
    message: str
    state: GameStateResponse
