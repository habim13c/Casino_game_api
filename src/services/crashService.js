const { randomInt } = require('../utils/random');

function generateCrashPoint() {
  // Generate crash point with house edge
  // Uses a provably fair algorithm concept
  const e = 2 ** 32;
  const h = randomInt(0, e);

  // 1% house edge
  if (h % 33 === 0) return 1.0; // instant crash (house edge)

  return Math.max(1, Math.floor((100 * e - h) / (e - h)) / 100);
}

function playCrash(betAmount, autoCashout) {
  const crashPoint = generateCrashPoint();
  const cashoutAt = Math.max(1.01, autoCashout);

  const won = cashoutAt <= crashPoint;
  const multiplier = won ? cashoutAt : 0;
  const winAmount = betAmount * multiplier;

  return {
    winAmount,
    result: {
      crashPoint,
      cashoutAt,
      won,
      winMultiplier: multiplier,
    }
  };
}

module.exports = { playCrash };
