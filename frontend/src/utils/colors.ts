/**
 * Generate a consistent color for a card based on its name or ID.
 * Uses a simple hash function to convert the string to a hue value.
 */
export function getCardColor(cardName: string): string {
  let hash = 0;
  for (let i = 0; i < cardName.length; i++) {
    hash = cardName.charCodeAt(i) + ((hash << 5) - hash);
    hash = hash & hash; // Convert to 32bit integer
  }

  // Convert hash to hue (0-360)
  const hue = Math.abs(hash % 360);

  // Use HSL for nice, vibrant colors
  // Saturation: 65-75% for rich but not overwhelming colors
  // Lightness: 55-65% for good contrast with white text
  const saturation = 65 + (Math.abs(hash % 10));
  const lightness = 55 + (Math.abs(hash % 10));

  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

/**
 * Get a darker shade of the card color for borders and accents
 */
export function getCardColorDark(cardName: string): string {
  let hash = 0;
  for (let i = 0; i < cardName.length; i++) {
    hash = cardName.charCodeAt(i) + ((hash << 5) - hash);
    hash = hash & hash;
  }

  const hue = Math.abs(hash % 360);
  const saturation = 70 + (Math.abs(hash % 10));
  const lightness = 35 + (Math.abs(hash % 10));

  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

/**
 * Get icon color based on icon type
 */
export function getIconColor(iconType: string): string {
  const iconColors: Record<string, string> = {
    'GEAR': '#9333ea',     // Purple
    'SPARK': '#eab308',    // Yellow/Gold
    'CHIP': '#3b82f6',     // Blue
    'HEART': '#ef4444',    // Red
    'None': '#6b7280',     // Gray
  };

  return iconColors[iconType] || iconColors['None'];
}
