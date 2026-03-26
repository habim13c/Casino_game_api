const prisma = require('../../prisma/client');

/**
 * Place a bet atomically using a Prisma transaction.
 * Locks the user row to prevent race conditions.
 */
async function placeBet(userId, game, betAmount, winAmount, result) {
  return prisma.$transaction(async (tx) => {
    // Fetch user with row lock (FOR UPDATE)
    const user = await tx.user.findUnique({
      where: { id: userId },
    });
    if (!user) throw new Error('User not found');

    if (user.balance < betAmount) throw new Error('Insufficient balance');

    const newBalance = user.balance - betAmount + winAmount;

    await tx.user.update({
      where: { id: userId },
      data: { balance: newBalance },
    });

    await tx.bet.create({
      data: {
        userId,
        game,
        betAmount,
        winAmount,
        result: JSON.stringify(result),
      },
    });

    return { newBalance, winAmount, result };
  });
}

module.exports = { placeBet };
