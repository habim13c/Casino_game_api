const { Prisma } = require('@prisma/client');

module.exports = (err, req, res, next) => {
  console.error(err);

  // Prisma errors
  if (err instanceof Prisma.PrismaClientKnownRequestError) {
    if (err.code === 'P2002') {
      return res.status(409).json({ error: 'A user with this email already exists' });
    }
    if (err.code === 'P2025') {
      return res.status(404).json({ error: 'Record not found' });
    }
  }

  // Zod validation errors
  if (err.name === 'ZodError') {
    return res.status(400).json({ error: err.errors });
  }

  // Custom business errors
  if (err.message === 'Insufficient balance') {
    return res.status(400).json({ error: err.message });
  }
  if (err.message === 'User not found') {
    return res.status(404).json({ error: err.message });
  }

  // Default server error
  res.status(500).json({ error: 'Internal server error' });
};
