import { GameState, Side, DrawSource } from '../types/game';

const API_BASE = '/game';

export interface CreateGameRequest {
  opponent: 'random' | 'greedy' | 'lookahead';
  seed?: number;
  max_turns?: number;
}

export interface CreateGameResponse {
  game_id: string;
  message: string;
  state: GameState;
}

export class GameAPI {
  static async createGame(request: CreateGameRequest): Promise<CreateGameResponse> {
    const response = await fetch(API_BASE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!response.ok) {
      throw new Error(`Failed to create game: ${response.statusText}`);
    }
    return response.json();
  }

  static async getGameState(gameId: string): Promise<GameState> {
    const response = await fetch(`${API_BASE}/${gameId}`);
    if (!response.ok) {
      throw new Error(`Failed to get game state: ${response.statusText}`);
    }
    return response.json();
  }

  static async submitAction(
    gameId: string,
    handIndex: number,
    side: Side,
    faceDown: boolean = false
  ): Promise<GameState> {
    const response = await fetch(`${API_BASE}/${gameId}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        hand_index: handIndex,
        side,
        face_down: faceDown,
      }),
    });
    if (!response.ok) {
      throw new Error(`Failed to submit action: ${response.statusText}`);
    }
    return response.json();
  }

  static async submitDraw(
    gameId: string,
    source: DrawSource,
    marketIndex?: number
  ): Promise<GameState> {
    const response = await fetch(`${API_BASE}/${gameId}/draw`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source,
        market_index: marketIndex,
      }),
    });
    if (!response.ok) {
      throw new Error(`Failed to submit draw: ${response.statusText}`);
    }
    return response.json();
  }

  static async submitEffectChoice(
    gameId: string,
    choice: number | string | boolean
  ): Promise<GameState> {
    const response = await fetch(`${API_BASE}/${gameId}/effect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ choice }),
    });
    if (!response.ok) {
      throw new Error(`Failed to submit effect choice: ${response.statusText}`);
    }
    return response.json();
  }

  static async deleteGame(gameId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/${gameId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(`Failed to delete game: ${response.statusText}`);
    }
  }
}
