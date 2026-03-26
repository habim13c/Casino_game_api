const { randomElement } = require('../utils/random');

const SYMBOLS = ['🍒', '🍋', '🍊', '🔔', '💎', '7'];

function spinReel() {
  return randomElement(SYMBOLS);
}

function calculateSlotWin(reels) {
  const [a, b, c] = reels;
  if (a === '7' && b === '7' && c === '7') return 10;
  if (a === '💎' && b === '💎' && c === '💎') return 5;
  if (a === b && b === c) return 3;
  if ((a === '7' && b === '7') || (b === '7' && c === '7') || (a === '7' && c === '7')) return 1;
  return 0;
}

function playSlot(betAmount) {
  const reels = [spinReel(), spinReel(), spinReel()];
  const multiplier = calculateSlotWin(reels);
  const winAmount = betAmount * multiplier;
  const result = {
    reels,
    winMultiplier: multiplier,
    winAmount,
  };
  return { winAmount, result };
}

module.exports = { playSlot };
