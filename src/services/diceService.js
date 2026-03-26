const { randomInt } = require('../utils/random');

function rollDice() {
  return { die1: randomInt(1, 7), die2: randomInt(1, 7) };
}

function playDice(betAmount, betType, value) {
  const { die1, die2 } = rollDice();
  const sum = die1 + die2;
  const isDoubles = die1 === die2;
  let multiplier = 0;

  switch (betType) {
    case 'over':
      // Over 7
      multiplier = sum > 7 ? 2 : 0;
      break;
    case 'under':
      // Under 7
      multiplier = sum < 7 ? 2 : 0;
      break;
    case 'exact':
      // Exact sum (pays 5×)
      multiplier = sum === parseInt(value) ? 5 : 0;
      break;
    case 'doubles':
      // Any doubles (pays 5×)
      multiplier = isDoubles ? 5 : 0;
      break;
    case 'seven':
      // Exactly 7 (pays 4×)
      multiplier = sum === 7 ? 4 : 0;
      break;
    default:
      multiplier = 0;
  }

  const winAmount = betAmount * multiplier;

  return {
    winAmount,
    result: {
      die1,
      die2,
      sum,
      isDoubles,
      betType,
      value,
      winMultiplier: multiplier,
    }
  };
}

module.exports = { playDice };
