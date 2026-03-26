const prisma = require('../../prisma/client');
const { depositSchema, withdrawSchema } = require('../utils/validationSchemas');

exports.getBalance = async (req, res, next) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.userId },
      select: { balance: true },
    });
    if (!user) return res.status(404).json({ error: 'User not found' });
    res.json({ balance: user.balance });
  } catch (err) {
    next(err);
  }
};

exports.deposit = async (req, res, next) => {
  try {
    const { amount } = depositSchema.parse(req.body);

    const updatedUser = await prisma.user.update({
      where: { id: req.userId },
      data: { balance: { increment: amount } },
    });

    res.json({ balance: updatedUser.balance });
  } catch (err) {
    next(err);
  }
};

exports.withdraw = async (req, res, next) => {
  try {
    const { amount } = withdrawSchema.parse(req.body);

    // Use transaction to check balance atomically
    const updatedUser = await prisma.$transaction(async (tx) => {
      const user = await tx.user.findUnique({
        where: { id: req.userId },
      });
      if (user.balance < amount) throw new Error('Insufficient balance');

      return tx.user.update({
        where: { id: req.userId },
        data: { balance: { decrement: amount } },
      });
    });

    res.json({ balance: updatedUser.balance });
  } catch (err) {
    next(err);
  }
};
