const { z } = require('zod');

// Common schemas
const emailSchema = z.string().email();
const passwordSchema = z.string().min(6);
const amountSchema = z.number().positive();

// Auth
const registerSchema = z.object({
  email: emailSchema,
  password: passwordSchema,
});

const loginSchema = z.object({
  email: emailSchema,
  password: z.string(),
});

// User
const depositSchema = z.object({
  amount: amountSchema,
});

const withdrawSchema = z.object({
  amount: amountSchema,
});

// Slot
const slotBetSchema = z.object({
  betAmount: amountSchema,
});

// Roulette bet types
const rouletteBetSchema = z.object({
  betAmount: amountSchema,
  betType: z.enum(['straight', 'color', 'parity', 'dozen']),
  value: z.union([z.number().int().min(0).max(36), z.string()]),
}).refine(data => {
  if (data.betType === 'straight') {
    return typeof data.value === 'number' && data.value >= 0 && data.value <= 36;
  }
  if (data.betType === 'color') {
    return ['red', 'black'].includes(data.value);
  }
  if (data.betType === 'parity') {
    return ['even', 'odd'].includes(data.value);
  }
  if (data.betType === 'dozen') {
    return ['1-18', '19-36'].includes(data.value);
  }
  return false;
}, { message: 'Invalid value for the given bet type' });

// Blackjack
const blackjackBetSchema = z.object({
  betAmount: amountSchema,
});

// Dice
const diceBetSchema = z.object({
  betAmount: amountSchema,
  betType: z.enum(['over', 'under', 'exact', 'doubles', 'seven']),
  value: z.number().int().min(2).max(12).optional(),
});

// Coin Flip
const coinFlipBetSchema = z.object({
  betAmount: amountSchema,
  choice: z.enum(['heads', 'tails']),
});

// Mines
const minesBetSchema = z.object({
  betAmount: amountSchema,
  minesCount: z.number().int().min(1).max(24),
  tilesRevealed: z.number().int().min(1).max(24),
});

// Crash
const crashBetSchema = z.object({
  betAmount: amountSchema,
  autoCashout: z.number().min(1.01),
});

// Plinko
const plinkoBetSchema = z.object({
  betAmount: amountSchema,
  risk: z.enum(['low', 'medium', 'high']),
});

// Hi-Lo
const hiloBetSchema = z.object({
  betAmount: amountSchema,
  guess: z.enum(['higher', 'lower']),
});

// Baccarat
const baccaratBetSchema = z.object({
  betAmount: amountSchema,
  betOn: z.enum(['player', 'banker', 'tie']),
});

module.exports = {
  registerSchema,
  loginSchema,
  depositSchema,
  withdrawSchema,
  slotBetSchema,
  rouletteBetSchema,
  blackjackBetSchema,
  diceBetSchema,
  coinFlipBetSchema,
  minesBetSchema,
  crashBetSchema,
  plinkoBetSchema,
  hiloBetSchema,
  baccaratBetSchema,
};
