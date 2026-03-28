# Test Credentials

## Admin Account
- Email: admin@casino.com
- Password: admin123
- Role: super_admin

## Test Player Account
- Email: testplayer@test.com
- Password: test123
- Role: player

## Additional Test Users
- Email: test@gmg.gg / testpassword (player)
- Email: fresh_user_test@gmg.gg / testpassword123 (player)

## API Endpoints Summary

### Auth
- POST /api/auth/register, login, logout
- GET /api/auth/me
- POST /api/auth/refresh

### Games (Instant)
- GET /api/games - List 18 games
- POST /api/games/{game}/play - Instant play

### Game Sessions (Interactive)
- POST /api/sessions/{game}/start - Start session (blackjack, mines, poker, hilo, crash)
- POST /api/sessions/{game}/{id}/action - Take action
- GET /api/sessions/{game}/active - Check active session

### Sportsbook Betting
- GET /api/betting/events, /sports, /live
- GET /api/betting/events/{id} - Event with markets
- POST /api/betting/place - Place bet
- POST /api/betting/cashout - Cash out
- GET /api/betting/my-bets

### Cricket
- GET /api/cricket/matches, /series, /live
- GET /api/cricket/matches/{id}/markets - 19 markets
- POST /api/cricket/matches/{id}/bet - Place bet
- GET /api/cricket/my-bets

### Admin
- GET /api/admin/dashboard, /users, /bets, /audit
- PATCH /api/admin/users/{id}/balance, /status
- PATCH /api/admin/games/{id}/config
- POST /api/admin/games/{id}/result, /cancel
- POST /api/admin/bulk/void-bets
- POST /api/admin/cricket/market/settle, /void
- GET /api/admin/reports/pnl, /activity
