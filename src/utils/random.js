const crypto = require('crypto');

/**
 * Returns a random integer between min (inclusive) and max (exclusive)
 */
function randomInt(min, max) {
  return crypto.randomInt(min, max);
}

/**
 * Picks a random element from an array
 */
function randomElement(arr) {
  const index = randomInt(0, arr.length);
  return arr[index];
}

module.exports = { randomInt, randomElement };
