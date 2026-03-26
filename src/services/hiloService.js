const { randomInt } = require('../utils/random');

function playHiLo(betAmount, guess) {
  const firstNumber = randomInt(1, 53);  // 1-52 (like a card deck)
  const secondNumber = randomInt(1, 53);

  let won = false;
  if (guess === 'higher') {
    won = secondNumber > firstNumber;
  } else if (guess === 'lower') {
    won = secondNumber < firstNumber;
  }
  // If equal, player loses

  // Payout based on probability of the guess being correct
  // Higher from low number = lower payout, higher from high number = higher payout
  let multiplier = 0;
  if (won) {
    if (guess === 'higher') {
      multiplier = Math.round((52 / (52 - firstNumber)) * 0.97 * 100) / 100;
    } else {
      multiplier = Math.round((52 / firstNumber) * 0.97 * 100) / 100;
    }
    multiplier = Math.max(1.01, Math.min(multiplier, 50)); // cap multiplier
  }

  const winAmount = betAmount * multiplier;

  return {
    winAmount,
    result: {
      firstNumber,
      secondNumber,
      guess,
      won,
      winMultiplier: multiplier,
    }
  };
}

module.exports = { playHiLo };
