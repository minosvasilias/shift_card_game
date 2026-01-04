export interface CardInfo {
  name: string;
  icon: string;
  type: string;
  description: string;
}

export interface CardInPlayInfo {
  card: CardInfo;
  face_down: boolean;
}

export interface PlayerStateInfo {
  hand: CardInfo[];
  row: CardInPlayInfo[];
  score: number;
}

export interface EffectChoiceInfo {
  choice_type: string;
  description: string;
  options: (number | string)[];
}

export interface GameState {
  game_id: string;
  current_turn: number;
  current_player: number;
  players: PlayerStateInfo[];
  market: CardInfo[];
  deck_size: number;
  is_game_over: boolean;
  winner: number | null;
  waiting_for: string | null;
  effect_choice_type: string | null;
  effect_choice: EffectChoiceInfo | null;
  game_log: ServerLogEntry[];
}

export interface GameLogEntry {
  id: string;
  timestamp: number;
  message: string;
  type: 'info' | 'action' | 'score' | 'effect';
}

export interface ServerLogEntry {
  log_type: string;
  player_idx: number;
  message: string;
  turn: number;
}

export type Side = 'LEFT' | 'RIGHT';
export type DrawSource = 'DECK' | 'MARKET';
