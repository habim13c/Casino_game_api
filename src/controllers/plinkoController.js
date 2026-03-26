const { placeBet } = require('../services/betService');
const { playPlinko } = require('../services/plinkoService');
const { plinkoBetSchema } = require('../utils/validationSchemas');

exports.play = async (req, res, next) => {
  try {
    const { betAmount, risk } = plinkoBetSchema.parse(req.body);
    const { winAmount, result } = playPlinko(betAmount, risk);
    const bet = await placeBet(req.userId, 'plinko', betAmount, winAmount, result);
    res.json({ balance: bet.newBalance, winAmount: bet.winAmount, result: bet.result });
  } catch (err) { next(err); }
};
