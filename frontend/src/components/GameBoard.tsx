import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GameState, Side, GameLogEntry, ServerLogEntry } from '../types/game';
import { GameAPI } from '../services/api';
import { Card } from './Card';
import { GameLog } from './GameLog';

// Map server log types to local log types
const mapLogType = (serverType: string): GameLogEntry['type'] => {
  switch (serverType) {
    case 'SCORE':
      return 'score';
    case 'CARD_PLAYED':
    case 'CARD_PUSHED':
    case 'DRAW':
      return 'action';
    case 'CENTER_TRIGGER':
    case 'EXIT_TRIGGER':
    case 'TRAP_TRIGGER':
    case 'EFFECT':
      return 'effect';
    case 'TURN_START':
    case 'GAME_END':
    default:
      return 'info';
  }
};

export function GameBoard() {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [gameLog, setGameLog] = useState<GameLogEntry[]>([]);
  const [selectedHandIndex, setSelectedHandIndex] = useState<number | null>(null);
  const [selectedSide, setSelectedSide] = useState<Side | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing] = useState(false);

  const addLog = useCallback((message: string, type: GameLogEntry['type'] = 'info') => {
    const entry: GameLogEntry = {
      id: `${Date.now()}-${Math.random()}`,
      timestamp: Date.now(),
      message,
      type,
    };
    setGameLog((prev) => [...prev, entry]);
  }, []);

  const addServerLogs = useCallback((serverLogs: ServerLogEntry[]) => {
    if (!serverLogs || serverLogs.length === 0) return;

    const newEntries: GameLogEntry[] = serverLogs.map((log, idx) => ({
      id: `${Date.now()}-${idx}-${Math.random()}`,
      timestamp: Date.now(),
      message: log.message,
      type: mapLogType(log.log_type),
    }));
    setGameLog((prev) => [...prev, ...newEntries]);
  }, []);

  const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  const startNewGame = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await GameAPI.createGame({
        opponent: 'greedy',
        max_turns: 10,
      });
      setGameState(response.state);
      setGameLog([]);
      addLog('Game started!', 'info');
      addServerLogs(response.state.game_log);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start game');
    } finally {
      setIsLoading(false);
    }
  };

  const playCard = async () => {
    if (!gameState || selectedHandIndex === null || !selectedSide || isProcessing) return;

    setIsLoading(true);
    setError(null);
    try {
      await delay(300);

      const newState = await GameAPI.submitAction(
        gameState.game_id,
        selectedHandIndex,
        selectedSide,
        false
      );

      await delay(400);

      setGameState(newState);
      setSelectedHandIndex(null);
      setSelectedSide(null);
      addServerLogs(newState.game_log);

      if (newState.waiting_for === 'draw') {
        addLog('Choose where to draw from', 'info');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to play card');
    } finally {
      setIsLoading(false);
    }
  };

  const drawCard = async (source: 'DECK' | 'MARKET', marketIndex?: number) => {
    if (!gameState || isProcessing) return;

    setIsLoading(true);
    setError(null);
    try {
      await delay(300);

      const newState = await GameAPI.submitDraw(
        gameState.game_id,
        source,
        marketIndex
      );

      await delay(400);

      setGameState(newState);
      addServerLogs(newState.game_log);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to draw card');
    } finally {
      setIsLoading(false);
    }
  };

  const submitEffectChoice = async (choice: number | string) => {
    if (!gameState || isProcessing) return;

    setIsLoading(true);
    setError(null);
    try {
      await delay(300);

      const newState = await GameAPI.submitEffectChoice(
        gameState.game_id,
        choice
      );

      await delay(400);

      setGameState(newState);
      addServerLogs(newState.game_log);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit choice');
    } finally {
      setIsLoading(false);
    }
  };

  // Helper to get display name for effect choice options
  const getEffectChoiceLabel = (option: number | string, choiceType: string): string => {
    if (choiceType === 'rewinder_market_card' || choiceType === 'market_draw') {
      const idx = typeof option === 'number' ? option : parseInt(option, 10);
      if (gameState && idx < gameState.market.length) {
        return gameState.market[idx].name;
      }
    }
    if (option === 'LEFT' || option === 'RIGHT') {
      return option;
    }
    if (option === 'SKIP') {
      return 'Skip';
    }
    return String(option);
  };

  useEffect(() => {
    startNewGame();
  }, []);

  if (!gameState) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">
          {isLoading ? 'Loading game...' : 'Initializing...'}
        </div>
      </div>
    );
  }

  const playerState = gameState.players[0];
  const opponentState = gameState.players[1];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-4">
      <div className="max-w-7xl mx-auto space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">Shift Card Game</h1>
          <div className="flex items-center gap-4">
            <div className="text-white text-sm">
              Turn {gameState.current_turn}/10
            </div>
            <button
              onClick={startNewGame}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold disabled:opacity-50"
            >
              New Game
            </button>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Opponent Area */}
        <div className="bg-gray-800/50 backdrop-blur rounded-lg p-4 border border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xl font-semibold text-white">
              Opponent {gameState.current_player === 1 && '(Active)'}
            </h2>
            <div className="text-2xl font-bold text-yellow-400">
              {opponentState.score} pts
            </div>
          </div>

          {/* Opponent Row */}
          <div className="flex gap-2 justify-center mb-4">
            <AnimatePresence mode="popLayout">
              {opponentState.row.map((cardInPlay, idx) => (
                <motion.div
                  key={`opp-${idx}-${cardInPlay.card.name}`}
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <Card
                    card={cardInPlay.card}
                    faceDown={cardInPlay.face_down}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {/* Opponent Hand (hidden) */}
          <div className="flex gap-2 justify-center">
            {opponentState.hand.map((_, idx) => (
              <div
                key={`opp-hand-${idx}`}
                className="w-20 h-28 bg-gray-700 rounded-lg border border-gray-600"
              />
            ))}
          </div>
        </div>

        {/* Market & Deck */}
        <div className="bg-gray-800/50 backdrop-blur rounded-lg p-4 border border-gray-700">
          <div className="flex items-center justify-between gap-4">
            {/* Deck */}
            <div className="flex flex-col items-center">
              <button
                onClick={() => drawCard('DECK')}
                disabled={gameState.waiting_for !== 'draw' || isLoading}
                className="w-32 h-44 bg-gradient-to-br from-indigo-600 to-indigo-800 rounded-lg shadow-lg border-2 border-indigo-500 flex flex-col items-center justify-center hover:scale-105 transition-transform disabled:opacity-50 disabled:hover:scale-100"
              >
                <div className="text-4xl text-white font-bold">{gameState.deck_size}</div>
                <div className="text-sm text-white/80 mt-2">DECK</div>
              </button>
            </div>

            {/* Market */}
            <div className="flex-1 flex flex-col items-center gap-2">
              <h3 className="text-white font-semibold">Market</h3>
              <div className="flex gap-2 justify-center">
                <AnimatePresence mode="popLayout">
                  {gameState.market.map((card, idx) => (
                    <motion.div
                      key={`market-${idx}-${card.name}`}
                      initial={{ scale: 0, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <Card
                        card={card}
                        onClick={() => gameState.waiting_for === 'draw' && !isLoading && drawCard('MARKET', idx)}
                        disabled={gameState.waiting_for !== 'draw' || isLoading}
                      />
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>
          </div>
        </div>

        {/* Player Area */}
        <div className="bg-gray-800/50 backdrop-blur rounded-lg p-4 border border-gray-700 border-t-4 border-t-green-500">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xl font-semibold text-white">
              You {gameState.current_player === 0 && '(Active)'}
            </h2>
            <div className="text-2xl font-bold text-green-400">
              {playerState.score} pts
            </div>
          </div>

          {/* Player Row with Side Selection */}
          <div className="mb-4">
            <div className="flex gap-4 justify-center items-center">
              {/* LEFT button */}
              <button
                onClick={() => {
                  if (selectedHandIndex !== null) {
                    setSelectedSide('LEFT');
                  }
                }}
                disabled={selectedHandIndex === null || gameState.waiting_for !== 'action' || isLoading}
                className={`px-6 py-12 rounded-lg font-bold text-white transition-all disabled:opacity-30 ${
                  selectedSide === 'LEFT'
                    ? 'bg-green-600 ring-4 ring-green-400'
                    : 'bg-gray-700 hover:bg-gray-600'
                }`}
              >
                LEFT →
              </button>

              {/* Player Row */}
              <div className="flex gap-2">
                <AnimatePresence mode="popLayout">
                  {playerState.row.map((cardInPlay, idx) => (
                    <motion.div
                      key={`player-${idx}-${cardInPlay.card.name}`}
                      initial={{ scale: 0, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <Card
                        card={cardInPlay.card}
                        faceDown={cardInPlay.face_down}
                      />
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>

              {/* RIGHT button */}
              <button
                onClick={() => {
                  if (selectedHandIndex !== null) {
                    setSelectedSide('RIGHT');
                  }
                }}
                disabled={selectedHandIndex === null || gameState.waiting_for !== 'action' || isLoading}
                className={`px-6 py-12 rounded-lg font-bold text-white transition-all disabled:opacity-30 ${
                  selectedSide === 'RIGHT'
                    ? 'bg-green-600 ring-4 ring-green-400'
                    : 'bg-gray-700 hover:bg-gray-600'
                }`}
              >
                ← RIGHT
              </button>
            </div>
          </div>

          {/* Player Hand */}
          <div className="flex gap-2 justify-center mb-4">
            {playerState.hand.map((card, idx) => (
              <Card
                key={`hand-${idx}-${card.name}`}
                card={card}
                onClick={() => {
                  if (gameState.waiting_for === 'action' && !isLoading) {
                    setSelectedHandIndex(idx);
                    setSelectedSide(null);
                  }
                }}
                selected={selectedHandIndex === idx}
                disabled={gameState.waiting_for !== 'action' || isLoading}
              />
            ))}
          </div>

          {/* Play Button */}
          {selectedHandIndex !== null && selectedSide !== null && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-center"
            >
              <button
                onClick={playCard}
                disabled={isLoading || isProcessing}
                className="px-8 py-4 bg-green-600 hover:bg-green-700 text-white rounded-lg font-bold text-lg shadow-lg disabled:opacity-50"
              >
                {isLoading ? 'Playing...' : 'Play Card'}
              </button>
            </motion.div>
          )}

          {/* Status Message */}
          <div className="text-center mt-3">
            {gameState.is_game_over ? (
              <div className="text-2xl font-bold text-yellow-400">
                Game Over! {gameState.winner === 0 ? '🎉 You Win!' : '😔 AI Wins'}
              </div>
            ) : gameState.waiting_for === 'action' ? (
              <div className="text-white">Select a card and a side to play</div>
            ) : gameState.waiting_for === 'draw' ? (
              <div className="text-white">Choose where to draw from</div>
            ) : gameState.waiting_for === 'effect' && gameState.effect_choice ? (
              <div className="space-y-3">
                <div className="text-white font-semibold">
                  {gameState.effect_choice.description}
                </div>
                <div className="flex gap-2 justify-center flex-wrap">
                  {gameState.effect_choice.options.map((option, idx) => (
                    <button
                      key={idx}
                      onClick={() => submitEffectChoice(option)}
                      disabled={isLoading}
                      className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold disabled:opacity-50 transition-colors"
                    >
                      {getEffectChoiceLabel(option, gameState.effect_choice!.choice_type)}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-gray-400">Waiting for opponent...</div>
            )}
          </div>
        </div>

        {/* Game Log */}
        <GameLog entries={gameLog} />
      </div>
    </div>
  );
}
