# NeonBet Casino Platform - PRD

## Original Problem Statement
Build a complete, production-ready casino backend system with a full game engine and betting system supporting 18 casino games, sportsbook betting, cricket live betting, wallet/payment system, user management with RBAC, and a comprehensive admin control panel.

## Architecture
- **Backend**: FastAPI (Python) on port 8001
- **Frontend**: React with Tailwind CSS on port 3000
- **Database**: MongoDB
- **Auth**: JWT (access + refresh tokens)
- **Design**: Neon dark theme ("Electric & Neon" archetype)

## What's Been Implemented

### Phase 1 - MVP (2026-03-28) ✅
- [x] JWT Authentication (register, login, logout, me, refresh)
- [x] Role-based access (player, admin, super_admin)
- [x] All 18 instant game engines with provably fair SHA-256
- [x] Wallet system (balance, deposit, withdraw, transactions)
- [x] Admin Dashboard (Overview, Users, Games, Bets, P&L, Audit)
- [x] React frontend with dark neon theme
- [x] Game lobby with search and category filters

### Phase 2 - Full Backend (2026-03-28) ✅
- [x] Interactive Game Sessions:
  - Blackjack: hit, stand, double, split
  - Mines: tile-by-tile reveal, cashout
  - Poker: hold/draw
  - Hi-Lo: chain guessing, cashout
  - Crash: auto/manual cashout
- [x] Sportsbook Betting Engine:
  - 21 pre-seeded events across 6 sports
  - Match winner, Over/Under, Handicap, Prop markets
  - Single and parlay bet types
  - Cash out functionality
  - Odds in Decimal/Fractional/American formats
- [x] Cricket Live Betting Module:
  - 12 matches across 4 series (T20/ODI/TEST)
  - 19 betting markets per match
  - Full match simulation engine (ball-by-ball)
  - Auto-settlement on simulation
  - Admin market settle/void controls
- [x] Jackpot/Progressive Pool System
- [x] Provably Fair Verification Endpoint
- [x] Enhanced Admin:
  - Game result override, cancel/void
  - Bulk void bets
  - Withdrawal approval workflow
  - User impersonation (read-only)
  - Active sessions monitoring
  - Cricket market settle/void
  - Maintenance mode per game
  - Activity reports

### Testing Status
- Phase 1 Backend: 100% pass
- Phase 2 Backend: 100% pass (35/35 tests)

## Prioritized Backlog

### P0 (Next Phase)
- [ ] Frontend pages for betting and cricket modules
- [ ] WebSocket for real-time game/betting updates
- [ ] Interactive game UI animations

### P1 (Important)
- [ ] 2FA for admins
- [ ] Stripe payment integration
- [ ] Bonus engine (wagering requirements)
- [ ] VIP tier automation
- [ ] Affiliate system

### P2 (Enhancement)
- [ ] Responsible gambling tools
- [ ] AML monitoring
- [ ] Docker/K8s configs
- [ ] Rate limiting
