require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');

const authMiddleware = require('./middleware/auth');
const errorHandler = require('./middleware/errorHandler');

const authController = require('./controllers/authController');
const userController = require('./controllers/userController');
const slotController = require('./controllers/slotController');
const rouletteController = require('./controllers/rouletteController');

const app = express();

// Security & logging
app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(morgan('combined'));

// Serve static assets (images, icons) to the frontend
app.use('/assets', express.static('public/assets'));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
});
app.use(limiter);

// Public routes
app.post('/api/auth/register', authController.register);
app.post('/api/auth/login', authController.login);

// Protected routes
app.use('/api/user', authMiddleware);
app.get('/api/user/balance', userController.getBalance);
app.post('/api/user/deposit', userController.deposit);
app.post('/api/user/withdraw', userController.withdraw);

app.use('/api/games/slot', authMiddleware);
app.post('/api/games/slot/bet', slotController.play);

app.use('/api/games/roulette', authMiddleware);
app.post('/api/games/roulette/bet', rouletteController.play);

// Health check
app.get('/health', (req, res) => res.json({ status: 'ok' }));

// Error handling (must be last)
app.use(errorHandler);

module.exports = app;
