const { placeBet } = require('../services/betService');
const { playSlot } = require('../services/slotService');
const { slotBetSchema } = require('../utils/validationSchemas');

exports.play = async (req, res, next) => {
  try {
    const { betAmount } = slotBetSchema.parse(req.body);

    // Play the game (deterministic outcome)
    const { winAmount, result } = playSlot(betAmount);

    // Execute atomic bet transaction
    const { newBalance, winAmount: finalWin, result: finalResult } = await placeBet(
      req.userId,
      'slot',
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
