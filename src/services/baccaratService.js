const { randomInt } = require('../utils/random');

function drawCard() {
  return randomInt(1, 10); // Baccarat card values 1-9 (10/J/Q/K = 0)
}

function handTotal(cards) {
  return cards.reduce((sum, c) => sum + c, 0) % 10;
}

function playBaccarat(betAmount, betOn) {
  // Deal initial 2 cards each
  const playerCards = [drawCard(), drawCard()];
  const bankerCards = [drawCard(), drawCard()];

  let playerTotal = handTotal(playerCards);
  let bankerTotal = handTotal(bankerCards);

  // Natural win check (8 or 9)
  const hasNatural = playerTotal >= 8 || bankerTotal >= 8;

  if (!hasNatural) {
    // Player third card rule
    let playerThirdCard = null;
    if (playerTotal <= 5) {
      playerThirdCard = drawCard();
      playerCards.push(playerThirdCard);
      playerTotal = handTotal(playerCards);
    }

    // Banker third card rule
    if (playerThirdCard === null) {
      // Player stood: banker draws on 0-5
      if (bankerTotal <= 5) {
        bankerCards.push(drawCard());
        bankerTotal = handTotal(bankerCards);
      }
    } else {
      // Complex banker rules based on player's third card
      const p3 = playerThirdCard;
      let bankerDraws = false;

      if (bankerTotal <= 2) bankerDraws = true;
      else if (bankerTotal === 3 && p3 !== 8) bankerDraws = true;
      else if (bankerTotal === 4 && [2, 3, 4, 5, 6, 7].includes(p3)) bankerDraws = true;
      else if (bankerTotal === 5 && [4, 5, 6, 7].includes(p3)) bankerDraws = true;
      else if (bankerTotal === 6 && [6, 7].includes(p3)) bankerDraws = true;

      if (bankerDraws) {
        bankerCards.push(drawCard());
        bankerTotal = handTotal(bankerCards);
      }
    }
  }

  // Determine winner
  let winner;
  if (playerTotal > bankerTotal) winner = 'player';
  else if (bankerTotal > playerTotal) winner = 'banker';
  else winner = 'tie';

  // Calculate payout
  let multiplier = 0;
  if (betOn === winner) {
    if (winner === 'player') multiplier = 2;        // 1:1
    else if (winner === 'banker') multiplier = 1.95; // 1:1 minus 5% commission
    else if (winner === 'tie') multiplier = 9;       // 8:1
  }

  const winAmount = betAmount * multiplier;

  return {
    winAmount,
    result: {
      playerCards,
      bankerCards,
      playerTotal,
      bankerTotal,
      winner,
      betOn,
      winMultiplier: multiplier,
    }
  };
}

module.exports = { playBaccarat };
