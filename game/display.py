"""Terminal display utilities for game visualization."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import GameState, CardInPlay, Side


# Box drawing characters
BOX_H = "─"
BOX_V = "│"
BOX_TL = "┌"
BOX_TR = "┐"
BOX_BL = "└"
BOX_BR = "┘"
BOX_T = "┬"
BOX_B = "┴"

# Card slot width
SLOT_WIDTH = 18


def _icon_symbol(icon) -> str:
    """Get a symbol for an icon."""
    from .state import Icon
    if icon is None:
        return "◯"
    return {
        Icon.GEAR: "⚙",
        Icon.SPARK: "⚡",
        Icon.CHIP: "◈",
        Icon.HEART: "♥",
    }.get(icon, "?")


def _format_card_slot(card: CardInPlay | None, is_center: bool = False) -> list[str]:
    """Format a single card slot as lines of text."""
    width = SLOT_WIDTH

    if card is None:
        # Empty slot
        return [
            f"{'':^{width}}",
            f"{'[ empty ]':^{width}}",
            f"{'':^{width}}",
        ]

    if not card.face_up:
        # Face-down card (trap)
        return [
            f"{'? ? ? ?':^{width}}",
            f"{'[HIDDEN]':^{width}}",
            f"{'? ? ? ?':^{width}}",
        ]

    # Face-up card
    icon = _icon_symbol(card.card.icon)
    name = card.card.name[:width-2]

    # Center marker
    center_mark = "★" if is_center else " "

    # Show last score if available
    score_info = ""
    if "last_center_score" in card.metadata:
        score_info = f"+{card.metadata['last_center_score']}"

    return [
        f"{icon}{center_mark}{score_info:>{width-3}}",
        f"{name:^{width}}",
        f"{'':^{width}}",
    ]


def format_row(row: list[CardInPlay], player_name: str = "Player") -> str:
    """Format a player's row as ASCII art."""
    lines = []

    # Pad row to 3 slots for display
    display_row: list[CardInPlay | None] = [None, None, None]
    for i, card in enumerate(row):
        if i < 3:
            display_row[i] = card

    # Determine center position
    has_center = len(row) == 3

    # Build the display
    slot_lines = []
    for i, card in enumerate(display_row):
        is_center = has_center and i == 1
        slot_lines.append(_format_card_slot(card, is_center))

    # Top border
    top = BOX_TL + BOX_H * SLOT_WIDTH + BOX_T + BOX_H * SLOT_WIDTH + BOX_T + BOX_H * SLOT_WIDTH + BOX_TR
    lines.append(top)

    # Card content (3 lines per slot)
    for line_idx in range(3):
        row_content = BOX_V
        for slot_idx in range(3):
            row_content += slot_lines[slot_idx][line_idx] + BOX_V
        lines.append(row_content)

    # Bottom border
    bottom = BOX_BL + BOX_H * SLOT_WIDTH + BOX_B + BOX_H * SLOT_WIDTH + BOX_B + BOX_H * SLOT_WIDTH + BOX_BR
    lines.append(bottom)

    # Position labels
    labels = f"  {'LEFT':^{SLOT_WIDTH}}  {'CENTER':^{SLOT_WIDTH}}  {'RIGHT':^{SLOT_WIDTH}}"
    lines.append(labels)

    return "\n".join(lines)


def format_market(market: list) -> str:
    """Format the market display."""
    lines = []
    lines.append("┌" + "─" * 40 + "┐")
    lines.append("│" + " MARKET ".center(40) + "│")
    lines.append("├" + "─" * 40 + "┤")

    if not market:
        lines.append("│" + " (empty) ".center(40) + "│")
    else:
        for i, card in enumerate(market):
            icon = _icon_symbol(card.icon)
            card_str = f" {i+1}. {icon} {card.name}"
            lines.append("│" + f"{card_str:<40}" + "│")

    lines.append("└" + "─" * 40 + "┘")
    return "\n".join(lines)


def format_hand(hand: list, player_name: str = "Player") -> str:
    """Format a player's hand."""
    if not hand:
        return f"  Hand: (empty)"

    cards = []
    for i, card in enumerate(hand):
        icon = _icon_symbol(card.icon)
        cards.append(f"{i+1}. {icon} {card.name}")

    return f"  Hand: " + " | ".join(cards)


def format_game_state(state: GameState, show_hands: bool = True) -> str:
    """Format the complete game state for terminal display."""
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append(f"  TURN {state.turn_counter}  |  Current Player: P{state.current_player}")
    lines.append("=" * 60)
    lines.append("")

    # Player 0
    p0 = state.players[0]
    lines.append(f"  PLAYER 0  [Score: {p0.score}]")
    lines.append(format_row(p0.row, "P0"))
    if show_hands:
        lines.append(format_hand(p0.hand, "P0"))
    lines.append("")

    # Market
    lines.append(format_market(state.market))
    lines.append("")

    # Player 1
    p1 = state.players[1]
    lines.append(f"  PLAYER 1  [Score: {p1.score}]")
    lines.append(format_row(p1.row, "P1"))
    if show_hands:
        lines.append(format_hand(p1.hand, "P1"))
    lines.append("")

    # Deck info
    lines.append(f"  Deck: {len(state.deck)} cards remaining")

    return "\n".join(lines)


def format_action(player_idx: int, card_name: str, side, face_down: bool = False) -> str:
    """Format a play action description."""
    from .state import Side
    side_str = "LEFT" if side == Side.LEFT else "RIGHT"
    hidden = " (face-down)" if face_down else ""
    return f"  → P{player_idx} plays [{card_name}] to {side_str}{hidden}"


def format_push(card_name: str, points: int = 0) -> str:
    """Format a push event."""
    if points > 0:
        return f"  ← Pushed out: [{card_name}] (scored {points} pts)"
    return f"  ← Pushed out: [{card_name}]"


def format_center_score(card_name: str, points: int) -> str:
    """Format a center scoring event."""
    return f"  ★ Center trigger: [{card_name}] scores {points} pts"


def format_draw(player_idx: int, source: str, card_name: str | None = None) -> str:
    """Format a draw action."""
    if card_name:
        return f"  ↓ P{player_idx} draws [{card_name}] from {source}"
    return f"  ↓ P{player_idx} draws from {source}"


def format_game_end(state: GameState, winner: int | None) -> str:
    """Format the game end summary."""
    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("  GAME OVER")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"  Final Scores:")
    lines.append(f"    Player 0: {state.players[0].score}")
    lines.append(f"    Player 1: {state.players[1].score}")
    lines.append("")

    if winner is None:
        lines.append("  Result: TIE!")
    else:
        lines.append(f"  Result: PLAYER {winner} WINS!")

    lines.append("")
    return "\n".join(lines)
