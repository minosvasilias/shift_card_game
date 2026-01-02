import { motion } from 'framer-motion';
import { CardInfo } from '../types/game';
import { getCardColor, getCardColorDark, getIconColor } from '../utils/colors';

interface CardProps {
  card: CardInfo;
  faceDown?: boolean;
  onClick?: () => void;
  onDragStart?: (e: React.DragEvent) => void;
  onDragEnd?: (e: React.DragEvent) => void;
  draggable?: boolean;
  selected?: boolean;
  disabled?: boolean;
  small?: boolean;
}

export function Card({
  card,
  faceDown = false,
  onClick,
  onDragStart,
  onDragEnd,
  draggable = false,
  selected = false,
  disabled = false,
  small = false,
}: CardProps) {
  const cardColor = getCardColor(card.name);
  const cardColorDark = getCardColorDark(card.name);
  const iconColor = getIconColor(card.icon);

  const sizeClasses = small
    ? 'w-24 h-32 text-xs'
    : 'w-32 h-44 text-sm';

  if (faceDown) {
    return (
      <motion.div
        className={`${sizeClasses} rounded-lg shadow-lg flex items-center justify-center cursor-default relative overflow-hidden`}
        style={{
          background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
          border: '2px solid #475569',
        }}
        whileHover={{ scale: 1.02 }}
        transition={{ type: 'spring', stiffness: 400, damping: 20 }}
      >
        <div className="absolute inset-0 opacity-10">
          <div className="grid grid-cols-3 gap-1 p-2">
            {[...Array(9)].map((_, i) => (
              <div
                key={i}
                className="aspect-square rounded-sm bg-slate-400"
              />
            ))}
          </div>
        </div>
        <div className="text-slate-500 font-bold text-2xl">?</div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className={`${sizeClasses} rounded-lg shadow-lg flex flex-col p-2 cursor-pointer relative overflow-hidden ${
        disabled ? 'opacity-50 cursor-not-allowed' : ''
      } ${selected ? 'ring-4 ring-yellow-400' : ''}`}
      style={{
        background: `linear-gradient(135deg, ${cardColor} 0%, ${cardColorDark} 100%)`,
        border: `2px solid ${cardColorDark}`,
      }}
      onClick={disabled ? undefined : onClick}
      onDragStart={draggable && !disabled ? onDragStart : undefined}
      onDragEnd={draggable && !disabled ? onDragEnd : undefined}
      draggable={draggable && !disabled}
      whileHover={disabled ? {} : { scale: 1.05 }}
      whileTap={disabled ? {} : { scale: 0.95 }}
      transition={{ type: 'spring', stiffness: 400, damping: 20 }}
      layout
    >
      {/* Card Type Badge */}
      <div
        className={`absolute top-1 right-1 ${small ? 'text-xs px-1 py-0.5' : 'text-xs px-2 py-1'} rounded font-bold text-white shadow`}
        style={{ backgroundColor: cardColorDark }}
      >
        {card.type}
      </div>

      {/* Icon */}
      {card.icon !== 'None' && (
        <div
          className={`${small ? 'w-6 h-6 text-xs' : 'w-8 h-8 text-sm'} rounded-full flex items-center justify-center font-bold text-white shadow mb-1`}
          style={{ backgroundColor: iconColor }}
        >
          {card.icon[0]}
        </div>
      )}

      {/* Card Name */}
      <div className={`${small ? 'text-xs' : 'text-sm'} font-bold text-white mb-1 leading-tight line-clamp-2`}>
        {card.name}
      </div>

      {/* Effect Text */}
      {!small && (
        <div className="flex-1 text-xs text-white/90 overflow-y-auto leading-tight">
          {card.description}
        </div>
      )}

      {/* Tooltip for small cards */}
      {small && (
        <div className="absolute hidden group-hover:block bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-gray-900 text-white text-xs rounded shadow-lg z-50">
          {card.description}
        </div>
      )}
    </motion.div>
  );
}
