const { randomInt, randomElement } = require('../utils/random');

const SUITS = ['♠', '♥', '♦', '♣'];
const RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];

function createDeck() {
  const deck = [];
  for (const suit of SUITS) {
    for (const rank of RANKS) {
      deck.push({ rank, suit });
    }
  }
  return deck;
}

function shuffleDeck(deck) {
  const shuffled = [...deck];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = randomInt(0, i + 1);
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

function cardValue(card) {
  if (['J', 'Q', 'K'].includes(card.rank)) return 10;
  if (card.rank === 'A') return 11;
  return parseInt(card.rank);
}

function handValue(hand) {
  let total = hand.reduce((sum, card) => sum + cardValue(card), 0);
  let aces = hand.filter(c => c.rank === 'A').length;
  while (total > 21 && aces > 0) {
    total -= 10;
    aces--;
  }
  return total;
}

function cardToString(card) {
  return `${card.rank}${card.suit}`;
}

function playBlackjack(betAmount) {
  const deck = shuffleDeck(createDeck());
  let idx = 0;

  const playerHand = [deck[idx++], deck[idx++]];
  const dealerHand = [deck[idx++], deck[idx++]];

  // Player auto-strategy: stand on 17+, hit below 17
  while (handValue(playerHand) < 17) {
    playerHand.push(deck[idx++]);
  }

  const playerTotal = handValue(playerHand);

  // Check player bust
  if (playerTotal > 21) {
    return {
      winAmount: 0,
      result: {
        playerHand: playerHand.map(cardToString),
        dealerHand: dealerHand.map(cardToString),
        playerTotal,
        dealerTotal: handValue(dealerHand),
        outcome: 'player_bust',
      }
    };
  }

  // Dealer draws on 16 or less, stands on 17+
  while (handValue(dealerHand) < 17) {
    dealerHand.push(deck[idx++]);
  }

  const dealerTotal = handValue(dealerHand);
  let outcome, multiplier;

  if (dealerTotal > 21) {
    outcome = 'dealer_bust';
    multiplier = 2;
  } else if (playerTotal > dealerTotal) {
    outcome = 'player_wins';
    multiplier = 2;
  } else if (playerTotal < dealerTotal) {
    outcome = 'dealer_wins';
    multiplier = 0;
  } else {
    outcome = 'push';
    multiplier = 1; // tie: return bet
  }

  // Check for blackjack (21 with 2 cards)
  if (playerHand.length === 2 && playerTotal === 21) {
    outcome = 'blackjack';
    multiplier = 2.5;
  }

  const winAmount = betAmount * multiplier;

  return {
    winAmount,
    result: {
      playerHand: playerHand.map(cardToString),
      dealerHand: dealerHand.map(cardToString),
      playerTotal,
      dealerTotal,
      outcome,
      winMultiplier: multiplier,
    }
  };
}

module.exports = { playBlackjack };
