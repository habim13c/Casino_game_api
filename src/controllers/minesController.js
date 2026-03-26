const { placeBet } = require('../services/betService');
const { playMines } = require('../services/minesService');
const { minesBetSchema } = require('../utils/validationSchemas');

exports.play = async (req, res, next) => {
  try {
    const { betAmount, minesCount, tilesRevealed } = minesBetSchema.parse(req.body);
    const { winAmount, result } = playMines(betAmount, minesCount, tilesRevealed);
    const bet = await placeBet(req.userId, 'mines', betAmount, winAmount, result);
    res.json({ balance: bet.newBalance, winAmount: bet.winAmount, result: bet.result });
  } catch (err) { next(err); }
};
