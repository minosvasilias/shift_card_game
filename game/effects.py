"""Card effect implementations for all 24 cards."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import GameState, CardInPlay, Icon, Event
    from agents.base import Agent


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_adjacent_icons(state: GameState, player_idx: int, position: int) -> tuple[set, set]:
    """Get the effective icons of adjacent cards."""
    from .state import Icon
    row = state.players[player_idx].row
    left_icons: set[Icon] = set()
    right_icons: set[Icon] = set()

    if position > 0:
        left_icons = row[position - 1].effective_icons
    if position < len(row) - 1:
        right_icons = row[position + 1].effective_icons

    return left_icons, right_icons


def count_shared_icons_with_opponent(state: GameState, player_idx: int, card: CardInPlay) -> int:
    """Count how many cards in opponent's row share an icon with this card."""
    opponent_idx = 1 - player_idx
    opponent_row = state.players[opponent_idx].row
    my_icons = card.effective_icons

    count = 0
    for opp_card in opponent_row:
        if opp_card.effective_icons & my_icons:
            count += 1
    return count


def get_unique_icons_in_row(state: GameState, player_idx: int) -> set:
    """Get all unique icons in a player's row."""
    from .state import Icon
    icons: set[Icon] = set()
    for card in state.players[player_idx].row:
        icons |= card.effective_icons
    return icons


def enforce_hand_limit(state: GameState, player_idx: int, agent: Agent) -> list:
    """
    Enforce the hand limit of 2 cards, forcing immediate discards.
    (Synchronous version - for non-async contexts like direct effect testing)

    NOTE: This only works with sync agents (like SyncTestAgent).
    For async agents, use enforce_hand_limit_async() instead.

    Returns list of discarded card names for logging.
    """
    from .state import EffectChoice

    discarded = []
    hand = state.players[player_idx].hand

    while len(hand) > 2:
        choice = EffectChoice(
            choice_type="discard_hand",
            options=list(range(len(hand))),
            description="Choose which card to discard (hand limit is 2)",
        )
        # This assumes a sync agent - async agents must use enforce_hand_limit_async
        discard_idx = agent.choose_effect_option(state, player_idx, choice)
        discarded_card = hand.pop(discard_idx)
        discarded.append(discarded_card.name)

    return discarded


async def enforce_hand_limit_async(state: GameState, player_idx: int, agent: Agent) -> list:
    """
    Enforce the hand limit of 2 cards, forcing immediate discards.
    (Async version - for use in async game engine)

    Returns list of discarded card names for logging.
    """
    from .state import EffectChoice

    discarded = []
    hand = state.players[player_idx].hand

    while len(hand) > 2:
        choice = EffectChoice(
            choice_type="discard_hand",
            options=list(range(len(hand))),
            description="Choose which card to discard (hand limit is 2)",
        )
        discard_idx = await agent.choose_effect_option(state, player_idx, choice)
        discarded_card = hand.pop(discard_idx)
        discarded.append(discarded_card.name)

    return discarded


# =============================================================================
# CENTER-SCORING EFFECTS
# =============================================================================

def effect_calibration_unit(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 2 points."""
    return 2


def effect_loner_bot(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 4 if neither adjacent card shares an icon with this. Otherwise 0."""
    row = state.players[player_idx].row
    position = row.index(card)
    left_icons, right_icons = get_adjacent_icons(state, player_idx, position)
    my_icons = card.effective_icons

    # Check if any adjacent card shares an icon
    if (left_icons & my_icons) or (right_icons & my_icons):
        return 0
    return 4


def effect_copycat(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score points equal to the lower of adjacent cards' last center-scores."""
    row = state.players[player_idx].row
    position = row.index(card)
    left, right = state.get_adjacent_cards(player_idx, position)

    left_score = left.metadata.get("last_center_score", 0) if left else 0
    right_score = right.metadata.get("last_center_score", 0) if right else 0

    return min(left_score, right_score)


def effect_siphon_drone(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 3. Opponent also scores 2."""
    opponent_idx = 1 - player_idx
    state.players[opponent_idx].score += 2
    return 3


def effect_jealous_unit(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 2 per card in opponent's row that shares an icon with this card."""
    count = count_shared_icons_with_opponent(state, player_idx, card)
    return 2 * count


def effect_sequence_bot(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 3 if row has exactly three different icons. Otherwise 1."""
    icons = get_unique_icons_in_row(state, player_idx)
    return 3 if len(icons) == 3 else 1


async def effect_kickback(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 2. Then push this card one slot toward either edge (your choice).

    When Kickback pushes toward an edge, it displaces the card in that direction.
    If that card is at the edge, it gets pushed OUT of the row.

    Example with row [A, Kickback, B]:
    - Push LEFT: A is pushed out, result is [Kickback, B]
    - Push RIGHT: B is pushed out, result is [A, Kickback]
    """
    from .state import EffectChoice, Side

    row = state.players[player_idx].row
    position = row.index(card)

    # Determine valid push directions
    options = []
    if position > 0:  # Can push left (there's a card to displace)
        options.append(Side.LEFT)
    if position < len(row) - 1:  # Can push right (there's a card to displace)
        options.append(Side.RIGHT)

    if options:
        choice = EffectChoice(
            choice_type="kickback_direction",
            options=options,
            description="Choose which direction to push Kickback"
        )
        direction = await agent.choose_effect_option(state, player_idx, choice)

        # The card at the edge in the push direction gets pushed out
        # We mark this for the engine to handle (so exit effects trigger properly)
        if direction == Side.LEFT:
            # The leftmost card (position 0) will be pushed out
            pushed_card = row[0]
            # Shift kickback left by 1
            row.remove(card)
            row.insert(position - 1, card)
        else:
            # The rightmost card will be pushed out
            pushed_card = row[-1]
            # Shift kickback right by 1
            row.remove(card)
            row.insert(position, card)  # position is now where kickback goes (was position+1 before remove)

        # Store the pushed card for the engine to handle
        card.metadata["kickback_pushed_card"] = pushed_card

    return 2


def effect_patience_circuit(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Note the current turn number. At end of game, score turns elapsed."""
    card.metadata["patience_turn"] = state.turn_counter
    return 0  # Actual scoring happens at game end


async def effect_turncoat(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 2. Swap this card with one card in opponent's row."""
    from .state import EffectChoice

    opponent_idx = 1 - player_idx
    opponent_row = state.players[opponent_idx].row

    if not opponent_row:
        return 2

    # Let agent choose which card to swap with
    choice = EffectChoice(
        choice_type="turncoat_target",
        options=list(range(len(opponent_row))),
        description="Choose which opponent card to swap with"
    )
    target_idx = await agent.choose_effect_option(state, player_idx, choice)

    my_row = state.players[player_idx].row
    my_position = my_row.index(card)

    # Swap the cards
    opponent_card = opponent_row[target_idx]
    opponent_row[target_idx] = card
    my_row[my_position] = opponent_card

    return 2


def effect_void(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 2 per empty slot across both rows."""
    empty_slots = 0
    for p in state.players:
        empty_slots += 3 - len(p.row)
    return 2 * empty_slots


def effect_buddy_system(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 3 if there is exactly one other card in your row. Otherwise 0."""
    row = state.players[player_idx].row
    # "One other card" means row length is 2 (this card + one other)
    return 3 if len(row) == 2 else 0


def effect_mimic(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """This card's icon becomes the icon of the card to its left. Score 2."""
    row = state.players[player_idx].row
    position = row.index(card)

    if position > 0:
        left_card = row[position - 1]
        # Store the mimicked icon
        if left_card.icon:
            card.metadata["mimicked_icon"] = left_card.icon
            card.metadata["mimic_target"] = left_card
    return 2


async def effect_tug_of_war(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 1. Opponent must push out one of their edge cards if they have 3."""
    from .state import EffectChoice, Side

    opponent_idx = 1 - player_idx
    opponent_row = state.players[opponent_idx].row

    if len(opponent_row) == 3:
        # Opponent must choose which edge to push
        choice = EffectChoice(
            choice_type="tug_of_war_edge",
            options=[Side.LEFT, Side.RIGHT],
            description="Choose which edge card to push out"
        )
        # Get opponent's agent choice (we need to call opponent's agent)
        # For now, we'll mark this for engine to handle
        card.metadata["pending_tug_of_war"] = True

    return 1


def effect_hollow_frame(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 0. This card counts as having every icon for adjacency."""
    card.metadata["all_icons"] = True
    return 0


def effect_echo_chamber(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 0. If turn counter is even, score 4."""
    if state.turn_counter % 2 == 0:
        return 4
    return 0


def effect_one_shot(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 5. Remove this card from the game entirely."""
    row = state.players[player_idx].row
    row.remove(card)
    # Card is not added to market - just removed
    return 5


def effect_embargo(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 1. Market is locked until your next turn."""
    from .state import ActiveEffect

    state.active_effects.append(ActiveEffect(
        effect_type="embargo",
        player_idx=player_idx,
        expires_turn=state.turn_counter + 1  # Expires at start of your next turn
    ))
    return 1


async def effect_scavenger(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 0. Look at all face-down cards. May swap this with one of them."""
    from .state import EffectChoice

    # Find all face-down cards
    face_down_cards = []
    for p_idx, player in enumerate(state.players):
        for c_idx, c in enumerate(player.row):
            if not c.face_up:
                face_down_cards.append((p_idx, c_idx, c))

    if face_down_cards:
        choice = EffectChoice(
            choice_type="scavenger_swap",
            options=[None] + face_down_cards,  # None = don't swap
            description="Choose a face-down card to swap with, or skip"
        )
        selected = await agent.choose_effect_option(state, player_idx, choice)

        if selected is not None:
            target_player, target_idx, target_card = selected
            my_row = state.players[player_idx].row
            my_position = my_row.index(card)

            # Swap the cards
            state.players[target_player].row[target_idx] = card
            my_row[my_position] = target_card

    return 0


async def effect_magnet(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 1. Pull one card from market into an adjacent slot."""
    from .state import EffectChoice, Side

    if not state.market:
        return 1

    row = state.players[player_idx].row
    position = row.index(card)

    # Choose which market card
    choice = EffectChoice(
        choice_type="magnet_market_card",
        options=list(range(len(state.market))),
        description="Choose which market card to pull"
    )
    market_idx = await agent.choose_effect_option(state, player_idx, choice)

    # Choose which side to place it
    sides = []
    if position > 0:
        sides.append(Side.LEFT)
    if position < len(row) - 1:
        sides.append(Side.RIGHT)

    if sides:
        choice = EffectChoice(
            choice_type="magnet_side",
            options=sides,
            description="Choose which side to place the card"
        )
        side = await agent.choose_effect_option(state, player_idx, choice)

        pulled_card = state.market.pop(market_idx)
        from .state import CardInPlay as CIP
        new_card = CIP(card=pulled_card, face_up=True)

        if side == Side.LEFT:
            insert_pos = position
            # Push existing card out if needed
            if len(row) >= 3:
                # The card at position-1 gets pushed further left (out)
                pushed = row.pop(0)
                state.market.append(pushed.card)
            row.insert(position, new_card)
        else:
            insert_pos = position + 1
            if len(row) >= 3:
                pushed = row.pop(-1)
                state.market.append(pushed.card)
            row.insert(insert_pos, new_card)

    return 1


def effect_hot_potato(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 2. This card goes to opponent's hand."""
    opponent_idx = 1 - player_idx
    row = state.players[player_idx].row

    if card in row:
        row.remove(card)

    opponent_hand = state.players[opponent_idx].hand
    opponent_hand.append(card.card)

    # Mark that opponent needs immediate hand limit check
    # They cannot discard the card they just received (Hot Potato)
    state.pending_hand_limit_checks[opponent_idx] = card.card.name

    return 2


async def effect_parasite(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 4. Swap positions with a card in opponent's row."""
    from .state import EffectChoice

    opponent_idx = 1 - player_idx
    opponent_row = state.players[opponent_idx].row

    if not opponent_row:
        return 4

    # Let agent choose which opponent card to swap with
    choice = EffectChoice(
        choice_type="parasite_target",
        options=list(range(len(opponent_row))),
        description="Choose which opponent card to swap positions with"
    )
    target_idx = await agent.choose_effect_option(state, player_idx, choice)

    my_row = state.players[player_idx].row
    my_position = my_row.index(card)

    # Swap the cards
    opponent_card = opponent_row[target_idx]
    opponent_row[target_idx] = card
    my_row[my_position] = opponent_card

    return 4


def effect_auctioneer(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 2 per icon type in your hand that opponent doesn't have in their hand."""
    my_hand = state.players[player_idx].hand
    opponent_hand = state.players[1 - player_idx].hand

    # Get unique icons in each hand
    my_icons = set(c.icon for c in my_hand if c.icon is not None)
    opp_icons = set(c.icon for c in opponent_hand if c.icon is not None)

    # Count icons I have that opponent doesn't
    unique_icons = my_icons - opp_icons
    return 2 * len(unique_icons)


async def effect_chain_reaction(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 2. Then trigger the center effect of the card to your left (if face-up and CENTER)."""
    from .state import CardType
    import inspect

    row = state.players[player_idx].row
    position = row.index(card)

    score = 2

    # Check if there's a card to the left
    if position > 0:
        left_card = row[position - 1]
        # Only trigger if it's face-up and a CENTER card
        if left_card.face_up and left_card.card.card_type == CardType.CENTER:
            # Trigger the left card's effect
            result = left_card.card.effect(state, left_card, player_idx, agent)
            if inspect.isawaitable(result):
                additional_score = await result
            else:
                additional_score = result
            score += additional_score
            # Store the last score for cards like Copycat
            left_card.metadata["last_center_score"] = additional_score

    return score


def effect_time_bomb(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Store current turn number. Next time this triggers, score the turn difference."""
    stored_turn = card.metadata.get("time_bomb_turn")

    if stored_turn is None:
        # First trigger - store the turn
        card.metadata["time_bomb_turn"] = state.turn_counter
        return 0
    else:
        # Subsequent trigger - score the difference
        turns_elapsed = state.turn_counter - stored_turn
        # Update the stored turn for next time
        card.metadata["time_bomb_turn"] = state.turn_counter
        return turns_elapsed


def effect_compressor(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 5. Push both edge cards out of your row."""
    row = state.players[player_idx].row

    # Can only compress if we have 3 cards
    if len(row) == 3:
        # Get the edge cards (cards at positions 0 and 2)
        left_edge = row[0]
        right_edge = row[2]

        # Store them for the engine to handle (so exit effects trigger)
        card.metadata["compressor_pushed_cards"] = [left_edge, right_edge]

    return 5


async def effect_extraction(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 1. Take a card from opponent's row and add it to your hand."""
    from .state import EffectChoice

    opponent_idx = 1 - player_idx
    opponent_row = state.players[opponent_idx].row

    if not opponent_row:
        return 1

    # Let agent choose which opponent card to extract
    choice = EffectChoice(
        choice_type="extraction_target",
        options=list(range(len(opponent_row))),
        description="Choose which opponent card to extract to your hand"
    )
    target_idx = await agent.choose_effect_option(state, player_idx, choice)

    # Remove the card from opponent's row and add to your hand
    extracted_card = opponent_row.pop(target_idx)
    state.players[player_idx].hand.append(extracted_card.card)

    # Enforce hand limit if needed
    await enforce_hand_limit_async(state, player_idx, agent)

    return 1


async def effect_purge(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 1. Choose a card in opponent's row and trash it permanently."""
    from .state import EffectChoice

    opponent_idx = 1 - player_idx
    opponent_row = state.players[opponent_idx].row

    if not opponent_row:
        return 1

    # Let agent choose which opponent card to purge
    choice = EffectChoice(
        choice_type="purge_target",
        options=list(range(len(opponent_row))),
        description="Choose which opponent card to purge (trash permanently)"
    )
    target_idx = await agent.choose_effect_option(state, player_idx, choice)

    # Remove the card from opponent's row (don't add to market - permanently removed)
    opponent_row.pop(target_idx)

    return 1


async def effect_sniper(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 2. Choose any card in opponent's row and push it out (triggers exit effect)."""
    from .state import EffectChoice

    opponent_idx = 1 - player_idx
    opponent_row = state.players[opponent_idx].row

    if not opponent_row:
        return 2

    # Let agent choose which opponent card to snipe
    choice = EffectChoice(
        choice_type="sniper_target",
        options=list(range(len(opponent_row))),
        description="Choose which opponent card to snipe (push out)"
    )
    target_idx = await agent.choose_effect_option(state, player_idx, choice)

    # Mark the card to be pushed out (engine will handle exit effects)
    sniped_card = opponent_row[target_idx]
    card.metadata["sniper_target"] = sniped_card
    card.metadata["sniper_target_idx"] = target_idx
    card.metadata["sniper_opponent_idx"] = opponent_idx

    return 2


# =============================================================================
# EXIT-SCORING EFFECTS
# =============================================================================

def effect_farewell_unit(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 3 when pushed out."""
    return 3


async def effect_spite_module(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Opponent must push out one of their edge cards (no center-score)."""
    from .state import EffectChoice, Side

    opponent_idx = 1 - player_idx
    opponent_row = state.players[opponent_idx].row

    if opponent_row:
        # Opponent chooses which edge
        choice = EffectChoice(
            choice_type="spite_module_edge",
            options=[Side.LEFT, Side.RIGHT] if len(opponent_row) > 1 else [Side.LEFT],
            description="Choose which edge card to push out"
        )
        # This needs to be handled by engine to call opponent's agent
        card.metadata["pending_spite_module"] = True

    return 0


def effect_boomerang(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Return to your hand. Cannot play this next turn."""
    hand = state.players[player_idx].hand
    hand.append(card.card)

    # Mark the card as unplayable next turn
    from .state import ActiveEffect
    state.active_effects.append(ActiveEffect(
        effect_type="boomerang_cooldown",
        player_idx=player_idx,
        data={"card_name": card.name},
        expires_turn=state.turn_counter + 2
    ))

    return 0


def effect_donation_bot(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Goes directly to opponent's hand instead of market."""
    opponent_idx = 1 - player_idx
    opponent_hand = state.players[opponent_idx].hand
    opponent_hand.append(card.card)
    # Don't add to market - engine will handle this
    card.metadata["skip_market"] = True
    return 0


async def effect_rewinder(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Take one card from market into your hand. This card goes to market."""
    from .state import EffectChoice

    if state.market:
        choice = EffectChoice(
            choice_type="rewinder_market_card",
            options=list(range(len(state.market))),
            description="Choose which market card to take"
        )
        market_idx = await agent.choose_effect_option(state, player_idx, choice)

        taken_card = state.market.pop(market_idx)
        state.players[player_idx].hand.append(taken_card)

    # Card goes to market as normal (handled by engine)
    return 0


def effect_sacrificial_lamb(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Score 3. (Has no center effect—purely an exit card.)"""
    return 3


def effect_phoenix(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Go to top of deck instead of market. Score 2."""
    # Mark that this card should go to deck instead of market
    card.metadata["phoenix_to_deck"] = True
    return 2


async def effect_sabotage(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Opponent must trash an edge card from their row."""
    from .state import EffectChoice, Side

    opponent_idx = 1 - player_idx
    opponent_row = state.players[opponent_idx].row

    if opponent_row:
        # Opponent chooses which edge to trash
        choice = EffectChoice(
            choice_type="sabotage_edge",
            options=[Side.LEFT, Side.RIGHT] if len(opponent_row) > 1 else [Side.LEFT],
            description="Choose which edge card to trash"
        )
        # Mark for engine to handle (opponent's agent needs to decide)
        card.metadata["pending_sabotage"] = True

    return 0


def effect_roadblock(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Next turn, opponent cannot play to the side this exited from."""
    from .state import ActiveEffect

    # Determine which side this card exited from (stored by engine)
    exit_side = card.metadata.get("exit_side")

    if exit_side:
        state.active_effects.append(ActiveEffect(
            effect_type="roadblock",
            player_idx=1 - player_idx,  # Affects opponent
            data={"blocked_side": exit_side},
            expires_turn=state.turn_counter + 2  # Lasts until end of opponent's next turn
        ))

    return 0


async def effect_recruiter(state: GameState, card: CardInPlay, player_idx: int, agent: Agent) -> int:
    """Search deck for any card, add to hand, shuffle deck."""
    from .state import EffectChoice
    import random

    if state.deck:
        # Show all cards in deck
        choice = EffectChoice(
            choice_type="recruiter_search",
            options=list(range(len(state.deck))),
            description="Choose which card to take from deck"
        )
        deck_idx = await agent.choose_effect_option(state, player_idx, choice)

        # Take the chosen card
        chosen_card = state.deck.pop(deck_idx)
        state.players[player_idx].hand.append(chosen_card)

        # Shuffle the deck
        random.shuffle(state.deck)

        # Enforce hand limit if needed
        await enforce_hand_limit_async(state, player_idx, agent)

    return 0


# =============================================================================
# TRAP TRIGGER CHECKS
# =============================================================================

def trigger_tripwire(event: Event, state: GameState, card: CardInPlay, player_idx: int) -> bool:
    """Trigger when opponent scores from a center effect."""
    from .state import EventType
    return (
        event.event_type == EventType.CARD_SCORED and
        event.player_idx != player_idx and
        event.points > 0
    )


def trigger_false_flag(event: Event, state: GameState, card: CardInPlay, player_idx: int) -> bool:
    """Trigger when opponent takes a card from the market."""
    from .state import EventType
    return (
        event.event_type == EventType.CARD_DRAWN_MARKET and
        event.player_idx != player_idx
    )


def trigger_snare(event: Event, state: GameState, card: CardInPlay, player_idx: int) -> bool:
    """Trigger when opponent plays a card with same icon as your center card."""
    from .state import EventType

    if event.event_type != EventType.CARD_PLAYED or event.player_idx == player_idx:
        return False

    my_center = state.get_center_card(player_idx)
    if not my_center:
        return False

    return event.icon in my_center.effective_icons


def trigger_mirror_trap(event: Event, state: GameState, card: CardInPlay, player_idx: int) -> bool:
    """Trigger when opponent's center card scores."""
    from .state import EventType
    return (
        event.event_type == EventType.CARD_SCORED and
        event.player_idx != player_idx and
        event.points > 0
    )


# =============================================================================
# TRAP EFFECTS
# =============================================================================

def effect_tripwire(state: GameState, card: CardInPlay, player_idx: int, agent: Agent, event: Event) -> int:
    """Their score is cancelled. You score 1."""
    # Cancel the opponent's score (this needs to be handled specially by engine)
    card.metadata["cancel_score"] = event.points
    return 1


def effect_false_flag(state: GameState, card: CardInPlay, player_idx: int, agent: Agent, event: Event) -> int:
    """That card goes to your hand instead."""
    card.metadata["redirect_card"] = event.card_name
    return 0


def effect_snare(state: GameState, card: CardInPlay, player_idx: int, agent: Agent, event: Event) -> int:
    """Their card goes to market instead of their row."""
    card.metadata["snare_card"] = event.card_name
    return 0


def effect_mirror_trap(state: GameState, card: CardInPlay, player_idx: int, agent: Agent, event: Event) -> int:
    """You score the same amount."""
    return event.points


def trigger_ambush(event: Event, state: GameState, card: CardInPlay, player_idx: int) -> bool:
    """Trigger when opponent plays a card to the same side this trap was played."""
    from .state import EventType

    if event.event_type != EventType.CARD_PLAYED or event.player_idx == player_idx:
        return False

    # Check if opponent played to the same side as this trap
    trap_side = card.metadata.get("trap_side")
    if trap_side and event.data.get("side") == trap_side:
        return True
    return False


def effect_ambush(state: GameState, card: CardInPlay, player_idx: int, agent: Agent, event: Event) -> int:
    """Steal the played card to your hand."""
    # Mark the card to be stolen (engine will handle the actual stealing)
    card.metadata["ambush_steal_card"] = event.card_name
    return 0


def trigger_tax_collector(event: Event, state: GameState, card: CardInPlay, player_idx: int) -> bool:
    """Trigger when opponent scores 4+ points in a single turn."""
    from .state import EventType
    return (
        event.event_type == EventType.CARD_SCORED and
        event.player_idx != player_idx and
        event.points >= 4
    )


def effect_tax_collector(state: GameState, card: CardInPlay, player_idx: int, agent: Agent, event: Event) -> int:
    """Nullify opponent's score."""
    # Mark the score to be cancelled (engine will handle this)
    card.metadata["cancel_score"] = event.points
    return 0


def trigger_mirror_match(event: Event, state: GameState, card: CardInPlay, player_idx: int) -> bool:
    """Trigger when opponent plays a card with same icon as this trap."""
    from .state import EventType

    if event.event_type != EventType.CARD_PLAYED or event.player_idx == player_idx:
        return False

    # Check if the played card has the same icon as this trap
    return event.icon == card.card.icon


def effect_mirror_match(state: GameState, card: CardInPlay, player_idx: int, agent: Agent, event: Event) -> int:
    """Nullify opponent's card and score 1."""
    # Mark the card to be nullified (engine will handle this)
    card.metadata["nullify_card"] = event.card_name
    return 1
