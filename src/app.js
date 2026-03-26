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
const blackjackController = require('./controllers/blackjackController');
const diceController = require('./controllers/diceController');
const coinFlipController = require('./controllers/coinFlipController');
const minesController = require('./controllers/minesController');
const crashController = require('./controllers/crashController');
const plinkoController = require('./controllers/plinkoController');
const hiloController = require('./controllers/hiloController');
const baccaratController = require('./controllers/baccaratController');

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

// Game routes (all protected)
app.use('/api/games', authMiddleware);
app.post('/api/games/slot/bet', slotController.play);
app.post('/api/games/roulette/bet', rouletteController.play);
app.post('/api/games/blackjack/bet', blackjackController.play);
app.post('/api/games/dice/bet', diceController.play);
app.post('/api/games/coinflip/bet', coinFlipController.play);
app.post('/api/games/mines/bet', minesController.play);
app.post('/api/games/crash/bet', crashController.play);
app.post('/api/games/plinko/bet', plinkoController.play);
app.post('/api/games/hilo/bet', hiloController.play);
app.post('/api/games/baccarat/bet', baccaratController.play);

// Health check
app.get('/health', (req, res) => res.json({ status: 'ok' }));

// Error handling (must be last)
app.use(errorHandler);

module.exports = app;
