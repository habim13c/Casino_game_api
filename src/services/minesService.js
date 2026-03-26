const { randomInt } = require('../utils/random');

function generateMineField(gridSize, minesCount) {
  const totalTiles = gridSize * gridSize;
  const mines = new Set();
  while (mines.size < minesCount) {
    mines.add(randomInt(0, totalTiles));
  }
  return mines;
}

function calculateMinesMultiplier(gridSize, minesCount, tilesRevealed) {
  const totalTiles = gridSize * gridSize;
  const safeTiles = totalTiles - minesCount;

  if (tilesRevealed <= 0 || tilesRevealed > safeTiles) return 0;

  // Calculate multiplier based on probability
  let multiplier = 1;
  for (let i = 0; i < tilesRevealed; i++) {
    const remaining = totalTiles - i;
    const safeRemaining = safeTiles - i;
    multiplier *= remaining / safeRemaining;
  }

  // Apply a 3% house edge
  multiplier *= 0.97;

  return Math.round(multiplier * 100) / 100;
}

function playMines(betAmount, minesCount, tilesRevealed) {
  const gridSize = 5;
  const totalTiles = gridSize * gridSize;
  const safeTiles = totalTiles - minesCount;

  // Generate mine field
  const mines = generateMineField(gridSize, minesCount);

  // Simulate revealing tiles randomly (avoiding mines)
  const safePositions = [];
  for (let i = 0; i < totalTiles; i++) {
    if (!mines.has(i)) safePositions.push(i);
  }

  // Check if player could actually reveal that many tiles
  const actualRevealed = Math.min(tilesRevealed, safeTiles);
  const hitMine = tilesRevealed > safeTiles;

  let multiplier = 0;
  let winAmount = 0;

  if (!hitMine && actualRevealed > 0) {
    multiplier = calculateMinesMultiplier(gridSize, minesCount, actualRevealed);
    winAmount = betAmount * multiplier;
  }

  return {
    winAmount,
    result: {
      gridSize,
      minesCount,
      tilesRevealed: actualRevealed,
      hitMine,
      minePositions: Array.from(mines),
      winMultiplier: multiplier,
    }
  };
}

module.exports = { playMines };
