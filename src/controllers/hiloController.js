const { placeBet } = require('../services/betService');
const { playHiLo } = require('../services/hiloService');
const { hiloBetSchema } = require('../utils/validationSchemas');

exports.play = async (req, res, next) => {
  try {
    const { betAmount, guess } = hiloBetSchema.parse(req.body);
    const { winAmount, result } = playHiLo(betAmount, guess);
    const bet = await placeBet(req.userId, 'hilo', betAmount, winAmount, result);
    res.json({ balance: bet.newBalance, winAmount: bet.winAmount, result: bet.result });
  } catch (err) { next(err); }
};
