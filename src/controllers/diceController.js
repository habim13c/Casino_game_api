const { placeBet } = require('../services/betService');
const { playDice } = require('../services/diceService');
const { diceBetSchema } = require('../utils/validationSchemas');

exports.play = async (req, res, next) => {
  try {
    const { betAmount, betType, value } = diceBetSchema.parse(req.body);
    const { winAmount, result } = playDice(betAmount, betType, value);
    const bet = await placeBet(req.userId, 'dice', betAmount, winAmount, result);
    res.json({ balance: bet.newBalance, winAmount: bet.winAmount, result: bet.result });
  } catch (err) { next(err); }
};
