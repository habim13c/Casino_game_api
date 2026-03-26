const { randomInt } = require('../utils/random');

function playCoinFlip(betAmount, choice) {
  const outcomes = ['heads', 'tails'];
  const result = outcomes[randomInt(0, 2)];
  const won = result === choice;
  const multiplier = won ? 1.95 : 0;
  const winAmount = betAmount * multiplier;

  return {
    winAmount,
    result: {
      outcome: result,
      playerChoice: choice,
      won,
      winMultiplier: multiplier,
    }
  };
}

module.exports = { playCoinFlip };
