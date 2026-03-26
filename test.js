const URL = 'http://localhost:3000';

async function testAll() {
  try {
    console.log('--- Testing API Endpoints ---\n');

    // 1. Register
    const email = `testUser_${Date.now()}@example.com`;
    console.log(`[*] Registering user ${email}...`);
    const regRes = await fetch(`${URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: 'password123' })
    });
    let regData;
    try { regData = await regRes.json(); } catch(e) { regData = await regRes.text(); }
    console.log('Status:', regRes.status);
    console.log('Result:', regData);

    // 2. Login
    console.log(`\n[*] Logging in...`);
    const loginRes = await fetch(`${URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: 'password123' })
    });
    let loginData;
    try { loginData = await loginRes.json(); } catch(e) { loginData = await loginRes.text(); }
    console.log('Status:', loginRes.status);
    if(loginRes.status !== 200) {
        console.log('Login failed:', loginData);
        return;
    }
    console.log('Result: Token received');
    const token = loginData.token;

    const authHeaders = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };

    // 3. Deposit
    console.log(`\n[*] Depositing 1000...`);
    const depRes = await fetch(`${URL}/api/user/deposit`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({ amount: 1000 })
    });
    console.log('Status:', depRes.status);
    console.log('Result:', await depRes.json());

    // 4. Get Balance
    console.log(`\n[*] Getting Balance...`);
    const balRes = await fetch(`${URL}/api/user/balance`, {
      method: 'GET',
      headers: authHeaders
    });
    console.log('Status:', balRes.status);
    console.log('Result:', await balRes.json());

    // 5. Play Slot
    console.log(`\n[*] Playing Slot with bet 100...`);
    const slotRes = await fetch(`${URL}/api/games/slot/bet`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({ betAmount: 100 })
    });
    console.log('Status:', slotRes.status);
    console.log('Result:', await slotRes.json());

    // 6. Play Roulette
    console.log(`\n[*] Playing Roulette with bet 100 on red...`);
    const rRes = await fetch(`${URL}/api/games/roulette/bet`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({ betAmount: 100, betType: 'color', value: 'red' })
    });
    console.log('Status:', rRes.status);
    console.log('Result:', await rRes.json());

    // 7. Withdraw
    console.log(`\n[*] Withdrawing 100...`);
    const wRes = await fetch(`${URL}/api/user/withdraw`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({ amount: 100 })
    });
    console.log('Status:', wRes.status);
    console.log('Result:', await wRes.json());

    console.log('\n--- All Tests Finished ---');
  } catch (error) {
    console.error('Test Failed:', error);
  }
}

testAll();
