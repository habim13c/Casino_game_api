const { placeBet } = require('../services/betService');
const { playRoulette } = require('../services/rouletteService');
const { rouletteBetSchema } = require('../utils/validationSchemas');

exports.play = async (req, res, next) => {
  try {
    const { betAmount, betType, value } = rouletteBetSchema.parse(req.body);

    // Play the game
    const { winAmount, result } = playRoulette(betAmount, betType, value);

    // Execute atomic bet transaction
    const { newBalance, winAmount: finalWin, result: finalResult } = await placeBet(
      req.userId,
      'roulette',
      betAmount,
      winAmount,
      result
    );

    res.json({
      balance: newBalance,
      winAmount: finalWin,
      result: finalResult,
    });
  } catch (err) {
    next(err);
  }
};
