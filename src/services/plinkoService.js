const { randomInt } = require('../utils/random');

const PLINKO_MULTIPLIERS = {
  low:    [1.5, 1.2, 1.1, 1.0, 0.5, 1.0, 1.1, 1.2, 1.5],
  medium: [3.0, 1.5, 1.2, 0.8, 0.4, 0.8, 1.2, 1.5, 3.0],
  high:   [7.0, 3.0, 1.5, 0.5, 0.2, 0.5, 1.5, 3.0, 7.0],
};

function playPlinko(betAmount, risk) {
  const rows = 8; // 8 rows of pegs
  let position = 4; // start in the middle (0-8 range)

  const path = [position];

  // Ball bounces left or right at each row
  for (let i = 0; i < rows; i++) {
    const goRight = randomInt(0, 2) === 1;
    if (goRight) {
      position = Math.min(position + 1, 8);
    } else {
      position = Math.max(position - 1, 0);
    }
    path.push(position);
  }

  // Final slot determines multiplier
  const multipliers = PLINKO_MULTIPLIERS[risk] || PLINKO_MULTIPLIERS.low;
  const slot = Math.min(position, multipliers.length - 1);
  const multiplier = multipliers[slot];
  const winAmount = betAmount * multiplier;

  return {
    winAmount,
    result: {
      path,
      finalSlot: slot,
      risk,
      winMultiplier: multiplier,
    }
  };
}

module.exports = { playPlinko };
