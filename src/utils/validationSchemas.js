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
  // Validate value based on betType
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

module.exports = {
  registerSchema,
  loginSchema,
  depositSchema,
  withdrawSchema,
  slotBetSchema,
  rouletteBetSchema,
};
