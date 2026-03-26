const { placeBet } = require('../services/betService');
const { playCoinFlip } = require('../services/coinFlipService');
const { coinFlipBetSchema } = require('../utils/validationSchemas');

exports.play = async (req, res, next) => {
  try {
    const { betAmount, choice } = coinFlipBetSchema.parse(req.body);
    const { winAmount, result } = playCoinFlip(betAmount, choice);
    const bet = await placeBet(req.userId, 'coinflip', betAmount, winAmount, result);
    res.json({ balance: bet.newBalance, winAmount: bet.winAmount, result: bet.result });
  } catch (err) { next(err); }
};
