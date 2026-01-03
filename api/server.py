"""
FastAPI server for interactive Shift card game.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from api.models import (
    NewGameRequest,
    PlayActionRequest,
    DrawChoiceRequest,
    EffectChoiceRequest,
    GameStateResponse,
    GameCreatedResponse,
    CardInfo,
    CardInPlayInfo,
    PlayerStateInfo,
)
from api.session_manager import session_manager
from game.state import PlayAction, DrawChoice, Side, EffectChoice, GameState


app = FastAPI(
    title="Shift Card Game API",
    description="Interactive API for playing the Shift card game",
    version="1.0.0",
)


def serialize_card(card) -> CardInfo:
    """Convert a Card to CardInfo."""
    return CardInfo(
        name=card.name,
        icon=card.icon.name if card.icon else "None",
        type=card.card_type.name,
        description=card.effect_text,
    )


def serialize_card_in_play(card_in_play) -> CardInPlayInfo:
    """Convert a CardInPlay to CardInPlayInfo."""
    return CardInPlayInfo(
        card=serialize_card(card_in_play.card),
        face_down=not card_in_play.face_up,
    )


def serialize_player_state(player_state) -> PlayerStateInfo:
    """Convert a PlayerState to PlayerStateInfo."""
    return PlayerStateInfo(
        hand=[serialize_card(card) for card in player_state.hand],
        row=[serialize_card_in_play(cip) for cip in player_state.row],
        score=player_state.score,
    )


def serialize_game_state(
    game_id: str,
    state: GameState,
    waiting_for: str | None,
    effect_choice: EffectChoice | None,
    winner: int | None,
) -> GameStateResponse:
    """Convert a GameState to GameStateResponse."""
    return GameStateResponse(
        game_id=game_id,
        current_turn=state.turn_counter,
        current_player=state.current_player,
        players=[serialize_player_state(p) for p in state.players],
        market=[serialize_card(card) for card in state.market],
        deck_size=len(state.deck),
        is_game_over=state.game_over,
        winner=winner if state.game_over else None,
        waiting_for=waiting_for,
        effect_choice_type=effect_choice.choice_type if effect_choice else None,
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Shift Card Game API",
        "endpoints": {
            "POST /game": "Create a new game",
            "GET /game/{game_id}": "Get game state",
            "POST /game/{game_id}/action": "Submit a play action",
            "POST /game/{game_id}/draw": "Submit a draw choice",
            "POST /game/{game_id}/effect": "Submit an effect choice",
            "DELETE /game/{game_id}": "End a game",
        },
    }


@app.post("/game", response_model=GameCreatedResponse)
async def create_game(request: NewGameRequest):
    """Create a new game session."""
    try:
        session = await session_manager.create_game(
            opponent=request.opponent,
            seed=request.seed,
            max_turns=request.max_turns,
        )

        state = session.get_state()
        waiting_for = session.get_waiting_for()
        effect_choice = session.get_last_effect_choice()
        winner = session.get_winner()

        return GameCreatedResponse(
            game_id=session.game_id,
            message="Game created successfully",
            state=serialize_game_state(
                session.game_id,
                state,
                waiting_for,
                effect_choice,
                winner,
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/game/{game_id}", response_model=GameStateResponse)
async def get_game_state(game_id: str):
    """Get the current state of a game."""
    session = session_manager.get_game(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found")

    try:
        state = session.get_state()
        waiting_for = session.get_waiting_for()
        effect_choice = session.get_last_effect_choice()
        winner = session.get_winner()

        return serialize_game_state(
            game_id,
            state,
            waiting_for,
            effect_choice,
            winner,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/game/{game_id}/action", response_model=GameStateResponse)
async def submit_action(game_id: str, request: PlayActionRequest):
    """Submit a play action (which card to play and where)."""
    session = session_manager.get_game(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found")

    if session.get_waiting_for() != 'action':
        raise HTTPException(
            status_code=400,
            detail=f"Not waiting for action (waiting for: {session.get_waiting_for()})",
        )

    try:
        action = PlayAction(
            hand_index=request.hand_index,
            side=Side.LEFT if request.side == 'LEFT' else Side.RIGHT,
            face_down=request.face_down,
        )

        processed = await session.submit_action(action)
        if not processed:
            raise HTTPException(status_code=504, detail="Action processing timeout")

        # Wait for next state (game may need more input or AI may be playing)
        await session.wait_for_ready(timeout=5.0)

        state = session.get_state()
        waiting_for = session.get_waiting_for()
        effect_choice = session.get_last_effect_choice()
        winner = session.get_winner()

        return serialize_game_state(
            game_id,
            state,
            waiting_for,
            effect_choice,
            winner,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/game/{game_id}/draw", response_model=GameStateResponse)
async def submit_draw(game_id: str, request: DrawChoiceRequest):
    """Submit a draw choice (deck or market)."""
    session = session_manager.get_game(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found")

    if session.get_waiting_for() != 'draw':
        raise HTTPException(
            status_code=400,
            detail=f"Not waiting for draw (waiting for: {session.get_waiting_for()})",
        )

    try:
        if request.source == 'MARKET':
            # Market draw requires card selection - use atomic operation
            if request.market_index is None:
                raise HTTPException(
                    status_code=400,
                    detail="market_index is required when drawing from market",
                )
            processed = await session.submit_market_draw(request.market_index)
        else:
            # Deck draw is simple
            processed = await session.submit_draw(DrawChoice.DECK)

        if not processed:
            raise HTTPException(status_code=504, detail="Draw processing timeout")

        # Wait for next state
        await session.wait_for_ready(timeout=5.0)

        state = session.get_state()
        waiting_for = session.get_waiting_for()
        effect_choice = session.get_last_effect_choice()
        winner = session.get_winner()

        return serialize_game_state(
            game_id,
            state,
            waiting_for,
            effect_choice,
            winner,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/game/{game_id}/effect", response_model=GameStateResponse)
async def submit_effect_choice(game_id: str, request: EffectChoiceRequest):
    """Submit an effect choice (e.g., which card to swap)."""
    session = session_manager.get_game(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found")

    if session.get_waiting_for() != 'effect':
        raise HTTPException(
            status_code=400,
            detail=f"Not waiting for effect (waiting for: {session.get_waiting_for()})",
        )

    try:
        processed = await session.submit_effect_choice(request.choice)
        if not processed:
            raise HTTPException(status_code=504, detail="Effect processing timeout")

        # Wait for next state
        await session.wait_for_ready(timeout=5.0)

        state = session.get_state()
        waiting_for = session.get_waiting_for()
        effect_choice = session.get_last_effect_choice()
        winner = session.get_winner()

        return serialize_game_state(
            game_id,
            state,
            waiting_for,
            effect_choice,
            winner,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/game/{game_id}")
async def delete_game(game_id: str):
    """End a game and clean up resources."""
    success = session_manager.delete_game(game_id)
    if not success:
        raise HTTPException(status_code=404, detail="Game not found")

    return {"message": "Game deleted successfully"}


@app.on_event("startup")
async def startup_event():
    """Run on server startup."""
    print("🎮 Shift Card Game API server starting...")
    print("📝 Visit http://localhost:8000/docs for API documentation")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on server shutdown."""
    print("🛑 Shutting down server...")
    # Stop all active games
    for game_id in list(session_manager.sessions.keys()):
        session_manager.delete_game(game_id)
