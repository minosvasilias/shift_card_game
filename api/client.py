"""
Terminal client for playing the Shift card game via the API.
"""

import requests
import time
import sys
from typing import Dict, Any


API_BASE = "http://localhost:8000"


class GameClient:
    """Client for interacting with the game API from the terminal."""

    def __init__(self):
        self.game_id: str | None = None
        self.base_url = API_BASE

    def create_game(
        self,
        opponent: str = 'greedy',
        seed: int | None = None,
    ) -> Dict[str, Any]:
        """Create a new game."""
        response = requests.post(
            f"{self.base_url}/game",
            json={
                "opponent": opponent,
                "seed": seed,
                "max_turns": 10,
            },
        )
        response.raise_for_status()
        data = response.json()
        self.game_id = data['game_id']
        return data

    def get_state(self) -> Dict[str, Any]:
        """Get the current game state."""
        if not self.game_id:
            raise ValueError("No active game")

        response = requests.get(f"{self.base_url}/game/{self.game_id}")
        response.raise_for_status()
        return response.json()

    def submit_action(
        self,
        hand_index: int,
        side: str,
        face_down: bool = False,
    ) -> Dict[str, Any]:
        """Submit a play action."""
        if not self.game_id:
            raise ValueError("No active game")

        response = requests.post(
            f"{self.base_url}/game/{self.game_id}/action",
            json={
                "hand_index": hand_index,
                "side": side,
                "face_down": face_down,
            },
        )
        response.raise_for_status()
        return response.json()

    def submit_draw(
        self,
        source: str,
        market_index: int | None = None,
    ) -> Dict[str, Any]:
        """Submit a draw choice."""
        if not self.game_id:
            raise ValueError("No active game")

        response = requests.post(
            f"{self.base_url}/game/{self.game_id}/draw",
            json={
                "source": source,
                "market_index": market_index,
            },
        )
        response.raise_for_status()
        return response.json()

    def submit_effect_choice(self, choice: Any) -> Dict[str, Any]:
        """Submit an effect choice."""
        if not self.game_id:
            raise ValueError("No active game")

        response = requests.post(
            f"{self.base_url}/game/{self.game_id}/effect",
            json={"choice": choice},
        )
        response.raise_for_status()
        return response.json()

    def delete_game(self) -> None:
        """Delete the game."""
        if not self.game_id:
            return

        try:
            requests.delete(f"{self.base_url}/game/{self.game_id}")
        except Exception:
            pass


def display_card(card: Dict[str, Any]) -> str:
    """Format a card for display."""
    return f"{card['icon']} {card['name']}"


def display_card_in_play(card_in_play: Dict[str, Any]) -> str:
    """Format a card in play."""
    if card_in_play['face_down']:
        return "🂠 [FACE DOWN]"
    card = card_in_play['card']
    return f"{card['icon']} {card['name']}"


def display_state(state: Dict[str, Any]) -> None:
    """Display the current game state."""
    print("\n" + "=" * 80)
    print(f"Turn {state['current_turn']} | Current Player: Player {state['current_player']}")
    print("=" * 80)

    # Display market
    print("\n📦 MARKET:")
    for i, card in enumerate(state['market']):
        print(f"  [{i}] {display_card(card)}")

    print(f"\n🎴 DECK: {state['deck_size']} cards remaining")

    # Display both players
    for i, player in enumerate(state['players']):
        is_current = i == state['current_player']
        marker = "👉 " if is_current else "   "
        print(f"\n{marker}PLAYER {i} (Score: {player['score']})")

        # Hand (only show for player 0 - the human)
        if i == 0:
            print("  Hand:")
            for j, card in enumerate(player['hand']):
                print(f"    [{j}] {display_card(card)}")
        else:
            print(f"  Hand: {len(player['hand'])} cards")

        # Row
        print("  Row:")
        if player['row']:
            for j, card_in_play in enumerate(player['row']):
                pos = ['LEFT', 'CENTER', 'RIGHT'][j]
                print(f"    [{pos}] {display_card_in_play(card_in_play)}")
        else:
            print("    [empty]")

    print("\n" + "=" * 80)


def get_player_action(state: Dict[str, Any]) -> tuple[int, str, bool]:
    """Prompt the player for an action."""
    player = state['players'][0]

    print("\n🎯 Choose a card to play:")
    for i, card in enumerate(player['hand']):
        print(f"  {i}: {display_card(card)}")

    while True:
        try:
            choice = input("\nCard index (0-2): ").strip()
            hand_index = int(choice)
            if 0 <= hand_index < len(player['hand']):
                break
            print("Invalid index. Try again.")
        except (ValueError, KeyboardInterrupt):
            print("\nPlease enter a number 0-2.")

    while True:
        side = input("Side (L/R): ").strip().upper()
        if side in ['L', 'R']:
            side = 'LEFT' if side == 'L' else 'RIGHT'
            break
        print("Invalid side. Enter L or R.")

    face_down = False
    fd_input = input("Face down? (y/N): ").strip().lower()
    if fd_input == 'y':
        face_down = True

    return hand_index, side, face_down


def get_draw_choice(state: Dict[str, Any]) -> tuple[str, int | None]:
    """Prompt the player for a draw choice."""
    print("\n🎴 Choose where to draw from:")
    print("  D: Deck")
    print("  M: Market")

    while True:
        choice = input("\nChoice (D/M): ").strip().upper()
        if choice == 'D':
            return 'DECK', None
        elif choice == 'M':
            break
        print("Invalid choice. Enter D or M.")

    # Choose from market
    print("\n📦 Choose a card from the market:")
    for i, card in enumerate(state['market']):
        print(f"  {i}: {display_card(card)}")

    while True:
        try:
            idx = int(input("\nMarket index (0-2): ").strip())
            if 0 <= idx < len(state['market']):
                return 'MARKET', idx
            print("Invalid index.")
        except (ValueError, KeyboardInterrupt):
            print("\nPlease enter a number 0-2.")


def get_effect_choice(state: Dict[str, Any], effect_type: str) -> Any:
    """Prompt the player for an effect choice."""
    print(f"\n⚡ Effect choice needed: {effect_type}")

    if effect_type == 'MARKET_CARD':
        # This is handled by draw choice
        pass
    elif effect_type in ['ROW_CARD', 'OPPONENT_ROW_CARD']:
        print("Choose a card index from the row (0-2):")
        while True:
            try:
                idx = int(input("Index: ").strip())
                if 0 <= idx <= 2:
                    return idx
                print("Invalid index.")
            except (ValueError, KeyboardInterrupt):
                print("\nPlease enter a number.")
    elif effect_type == 'BOOLEAN':
        choice = input("Yes or No? (y/n): ").strip().lower()
        return choice == 'y'
    else:
        # Generic input
        return input(f"Enter choice for {effect_type}: ").strip()


def play_game():
    """Main game loop."""
    client = GameClient()

    print("🎮 Welcome to Shift Card Game!")
    print("\n⚙️  Starting new game...")

    try:
        # Create game
        result = client.create_game(opponent='greedy')
        print(f"✅ Game created: {result['game_id'][:8]}...")

        state = result['state']

        # Game loop
        while not state['is_game_over']:
            display_state(state)

            # Check what we're waiting for
            waiting_for = state.get('waiting_for')

            if waiting_for == 'action':
                # Player's turn to play a card
                hand_index, side, face_down = get_player_action(state)
                state = client.submit_action(hand_index, side, face_down)

            elif waiting_for == 'draw':
                # Player's turn to draw
                source, market_idx = get_draw_choice(state)
                state = client.submit_draw(source, market_idx)

            elif waiting_for == 'effect':
                # Player needs to make an effect choice
                effect_type = state.get('effect_choice_type', 'UNKNOWN')
                choice = get_effect_choice(state, effect_type)
                state = client.submit_effect_choice(choice)

            elif state['current_player'] == 1:
                # AI's turn - just wait for it to complete
                print("\n🤖 AI is thinking...")
                time.sleep(1)
                state = client.get_state()

            else:
                # Wait for state to update
                time.sleep(0.5)
                state = client.get_state()

        # Game over
        display_state(state)
        print("\n🎊 GAME OVER!")

        winner = state['winner']
        if winner is None:
            print("🤝 It's a tie!")
        elif winner == 0:
            print("🎉 You win!")
        else:
            print("😔 AI wins!")

        scores = [p['score'] for p in state['players']]
        print(f"\nFinal scores: You {scores[0]} - {scores[1]} AI")

    except KeyboardInterrupt:
        print("\n\n👋 Game interrupted!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        if client.game_id:
            print("\n🧹 Cleaning up...")
            client.delete_game()


if __name__ == '__main__':
    play_game()
