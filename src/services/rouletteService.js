const { randomInt } = require('../utils/random');

function spinRoulette() {
  return randomInt(0, 37); // 0 to 36 inclusive
}

function getColor(number) {
  if (number === 0) return 'green';
  const reds = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36];
  return reds.includes(number) ? 'red' : 'black';
}

function resolveBet(betType, value, winningNumber) {
  switch (betType) {
    case 'straight':
      return value === winningNumber ? 35 : 0;
    case 'color': {
      const color = getColor(winningNumber);
      return color === value ? 1 : 0;
    }
    case 'parity': {
      let parity;
      if (winningNumber === 0) parity = 'zero';
      else parity = winningNumber % 2 === 0 ? 'even' : 'odd';
      return parity === value ? 1 : 0;
    }
    case 'dozen': {
      let range;
      if (winningNumber === 0) range = 'zero';
      else range = winningNumber <= 18 ? '1-18' : '19-36';
      return range === value ? 1 : 0;
    }
    default:
      return 0;
  }
}

function playRoulette(betAmount, betType, value) {
  const winningNumber = spinRoulette();
  const multiplier = resolveBet(betType, value, winningNumber);
  const winAmount = betAmount * multiplier;
  const result = {
    winningNumber,
    betType,
    value,
    winMultiplier: multiplier,
  };
  return { winAmount, result };
}

module.exports = { playRoulette };
