# Test Credentials

## Admin Account
- Email: admin@casino.com
- Password: admin123
- Role: super_admin

## Test Player Account
- Email: testplayer@test.com
- Password: test123
- Role: player
- Starting Balance: $1,000 (welcome bonus)

## Auth Endpoints
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me
- POST /api/auth/refresh

## Game Endpoints
- GET /api/games - List all 18 games
- GET /api/games/{game_name} - Game info
- POST /api/games/{game_name}/play - Play game (requires auth)

## Admin Endpoints (requires admin role)
- GET /api/admin/dashboard
- GET /api/admin/users
- GET /api/admin/users/{id}
- PATCH /api/admin/users/{id}/balance
- PATCH /api/admin/users/{id}/status
- GET /api/admin/games/config
- PATCH /api/admin/games/{id}/config
- GET /api/admin/bets
- GET /api/admin/reports/pnl
- GET /api/admin/audit
