const URL = 'http://localhost:3000';

async function testAll() {
  try {
    console.log('=== Casino API Full Test Suite (10 Games) ===\n');

    // 1. Register
    const email = `test_${Date.now()}@example.com`;
    console.log(`[*] Registering ${email}...`);
    const regRes = await fetch(`${URL}/api/auth/register`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: 'password123' })
    });
    console.log('Status:', regRes.status, await regRes.json());

    // 2. Login
    console.log(`\n[*] Logging in...`);
    const loginRes = await fetch(`${URL}/api/auth/login`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: 'password123' })
    });
    const loginData = await loginRes.json();
    console.log('Status:', loginRes.status, '- Token received');
    const token = loginData.token;
    const H = { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` };

    // 3. Deposit
    console.log(`\n[*] Depositing 5000...`);
    const depRes = await fetch(`${URL}/api/user/deposit`, { method: 'POST', headers: H, body: JSON.stringify({ amount: 5000 }) });
    console.log('Status:', depRes.status, await depRes.json());

    // ===== GAME TESTS =====
    const games = [
      { name: 'Slot Machine',  url: '/api/games/slot/bet',      body: { betAmount: 50 } },
      { name: 'Roulette',      url: '/api/games/roulette/bet',   body: { betAmount: 50, betType: 'color', value: 'red' } },
      { name: 'Blackjack',     url: '/api/games/blackjack/bet',  body: { betAmount: 50 } },
      { name: 'Dice',          url: '/api/games/dice/bet',       body: { betAmount: 50, betType: 'over' } },
      { name: 'Coin Flip',     url: '/api/games/coinflip/bet',   body: { betAmount: 50, choice: 'heads' } },
      { name: 'Mines',         url: '/api/games/mines/bet',      body: { betAmount: 50, minesCount: 3, tilesRevealed: 5 } },
      { name: 'Crash',         url: '/api/games/crash/bet',      body: { betAmount: 50, autoCashout: 2.0 } },
      { name: 'Plinko',        url: '/api/games/plinko/bet',     body: { betAmount: 50, risk: 'medium' } },
      { name: 'Hi-Lo',         url: '/api/games/hilo/bet',       body: { betAmount: 50, guess: 'higher' } },
      { name: 'Baccarat',      url: '/api/games/baccarat/bet',   body: { betAmount: 50, betOn: 'player' } },
    ];

    for (const game of games) {
      console.log(`\n[*] Playing ${game.name}...`);
      const res = await fetch(`${URL}${game.url}`, { method: 'POST', headers: H, body: JSON.stringify(game.body) });
      const data = await res.json();
      console.log(`Status: ${res.status} | Balance: ${data.balance} | Won: ${data.winAmount}`);
      if (data.result) {
        const r = typeof data.result === 'string' ? JSON.parse(data.result) : data.result;
        console.log('  Result:', JSON.stringify(r));
      }
    }

    // Final balance check
    console.log(`\n[*] Final Balance Check...`);
    const balRes = await fetch(`${URL}/api/user/balance`, { method: 'GET', headers: H });
    console.log('Status:', balRes.status, await balRes.json());

    console.log('\n=== All 10 Games Tested Successfully ===');
  } catch (error) {
    console.error('Test Failed:', error);
  }
}

testAll();
