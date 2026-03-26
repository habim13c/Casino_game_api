const { placeBet } = require('../services/betService');
const { playBaccarat } = require('../services/baccaratService');
const { baccaratBetSchema } = require('../utils/validationSchemas');

exports.play = async (req, res, next) => {
  try {
    const { betAmount, betOn } = baccaratBetSchema.parse(req.body);
    const { winAmount, result } = playBaccarat(betAmount, betOn);
    const bet = await placeBet(req.userId, 'baccarat', betAmount, winAmount, result);
    res.json({ balance: bet.newBalance, winAmount: bet.winAmount, result: bet.result });
  } catch (err) { next(err); }
};
