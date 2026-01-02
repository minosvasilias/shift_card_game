import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GameLogEntry } from '../types/game';

interface GameLogProps {
  entries: GameLogEntry[];
}

export function GameLog({ entries }: GameLogProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getLogColor = (type: GameLogEntry['type']) => {
    switch (type) {
      case 'score':
        return 'text-green-400';
      case 'action':
        return 'text-blue-400';
      case 'effect':
        return 'text-purple-400';
      default:
        return 'text-gray-400';
    }
  };

  const displayedEntries = isExpanded ? entries : entries.slice(-3);

  return (
    <div className="bg-gray-900/90 backdrop-blur rounded-lg shadow-xl border border-gray-700">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-800/50 transition-colors rounded-t-lg"
      >
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-white font-semibold">Game Log</span>
          <span className="text-gray-400 text-sm">({entries.length} events)</span>
        </div>
        <motion.svg
          className="w-5 h-5 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </motion.svg>
      </button>

      {/* Log Entries */}
      <AnimatePresence initial={false}>
        <motion.div
          initial={{ height: 0 }}
          animate={{ height: isExpanded ? 'auto' : '120px' }}
          exit={{ height: 0 }}
          transition={{ duration: 0.3 }}
          className="overflow-hidden"
        >
          <div className="px-4 pb-3 space-y-2 max-h-96 overflow-y-auto">
            {displayedEntries.length === 0 ? (
              <div className="text-gray-500 text-sm italic py-2">
                No events yet...
              </div>
            ) : (
              displayedEntries.map((entry) => (
                <motion.div
                  key={entry.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3 }}
                  className="text-sm"
                >
                  <span className="text-gray-600 text-xs mr-2">
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </span>
                  <span className={getLogColor(entry.type)}>
                    {entry.message}
                  </span>
                </motion.div>
              ))
            )}
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
