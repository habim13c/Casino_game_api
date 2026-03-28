# NeonBet Casino Platform - PRD

## Original Problem Statement
Build a complete, production-ready casino backend system with a full game engine and betting system supporting 18 casino games, sportsbook betting, cricket live betting, wallet/payment system, user management with RBAC, and a comprehensive admin control panel.

## Architecture
- **Backend**: FastAPI (Python) on port 8001
- **Frontend**: React with Tailwind CSS on port 3000
- **Database**: MongoDB
- **Auth**: JWT (access + refresh tokens)
- **Design**: Neon dark theme ("Electric & Neon" archetype)

## User Personas
1. **Player**: Registers, deposits, plays games, withdraws winnings
2. **Admin/Super-Admin**: Manages users, games, views reports, adjusts balances

## Core Requirements (Static)
- 18 casino games with provably fair (SHA-256) mechanics
- JWT auth with role-based access control
- Wallet with deposit/withdraw/transaction history
- Admin dashboard with user management, game config, P&L reports, audit log
- React frontend with game lobby, game play, wallet, profile, admin pages

## What's Been Implemented (2026-03-28)
### Phase 1 - MVP ✅
- [x] JWT Authentication (register, login, logout, me, refresh)
- [x] Role-based access (player, admin, super_admin)
- [x] All 18 game engines with provably fair system
  - Slots, Blackjack, Roulette, Crash, Mines, Poker, Craps, Sic Bo, Baccarat, Wheel of Fortune, Dragon Tiger, Video Poker, Hi-Lo, Plinko, Lottery, Teen Patti, Andar Bahar, Keno
- [x] Wallet system (balance, deposit, withdraw, transactions)
- [x] Bet history with pagination and filtering
- [x] Player profile with stats
- [x] Loyalty points system
- [x] Admin Dashboard (Overview, Users, Games, Bets, P&L, Audit tabs)
- [x] Admin user management (search, status change, balance adjustment)
- [x] Admin game configuration (enable/disable, house edge)
- [x] Admin P&L reports (GGR, NGR, hold %, by game)
- [x] Admin audit log
- [x] React frontend with dark neon theme
- [x] Game lobby with search and category filters
- [x] Individual game play pages with dynamic parameters
- [x] Welcome bonus ($1,000 on registration)

### Testing Status
- Backend: 100% pass rate
- Frontend: 85% pass rate (minor search fix applied)

## Prioritized Backlog

### P0 (Critical - Next Phase)
- [ ] Sportsbook betting engine (pre-match, live, parlays)
- [ ] Cricket live betting module with CricAPI integration
- [ ] WebSocket for real-time game updates
- [ ] Interactive game UIs (Blackjack card visuals, Roulette wheel animation)

### P1 (Important)
- [ ] Two-Factor Authentication (2FA)
- [ ] Password reset flow
- [ ] Stripe payment integration
- [ ] Crypto wallet integration
- [ ] Withdrawal approval workflow
- [ ] Bonus engine (wagering requirements, free spins)
- [ ] VIP tier system automation
- [ ] Affiliate system with commission tracking

### P2 (Enhancement)
- [ ] Jackpot/progressive pool system
- [ ] Responsible gambling tools (self-exclusion, limits)
- [ ] AML transaction monitoring
- [ ] Push notifications
- [ ] Real-time admin activity feed (WebSocket)
- [ ] Docker/Kubernetes deployment configs
- [ ] CI/CD pipeline
- [ ] Rate limiting per user
- [ ] Session management across devices

## Next Tasks
1. Add WebSocket support for real-time game updates
2. Build interactive game UIs (card animations, wheel spinning)
3. Implement sportsbook betting engine
4. Add Stripe payment integration
5. Build cricket live betting with simulation engine
