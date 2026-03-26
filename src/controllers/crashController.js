const { placeBet } = require('../services/betService');
const { playCrash } = require('../services/crashService');
const { crashBetSchema } = require('../utils/validationSchemas');

exports.play = async (req, res, next) => {
  try {
    const { betAmount, autoCashout } = crashBetSchema.parse(req.body);
    const { winAmount, result } = playCrash(betAmount, autoCashout);
    const bet = await placeBet(req.userId, 'crash', betAmount, winAmount, result);
    res.json({ balance: bet.newBalance, winAmount: bet.winAmount, result: bet.result });
  } catch (err) { next(err); }
};
