const { placeBet } = require('../services/betService');
const { playBlackjack } = require('../services/blackjackService');
const { blackjackBetSchema } = require('../utils/validationSchemas');

exports.play = async (req, res, next) => {
  try {
    const { betAmount } = blackjackBetSchema.parse(req.body);
    const { winAmount, result } = playBlackjack(betAmount);
    const bet = await placeBet(req.userId, 'blackjack', betAmount, winAmount, result);
    res.json({ balance: bet.newBalance, winAmount: bet.winAmount, result: bet.result });
  } catch (err) { next(err); }
};
