#!/usr/bin/env python3
"""
Comprehensive Casino Platform API Testing
Tests all 18 games, auth, wallet, and admin functionality
"""

import requests
import sys
import json
from datetime import datetime
import time

class CasinoAPITester:
    def __init__(self, base_url="https://cafd1537-671b-41f5-a582-2c457f3b80d3.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.admin_token = None
        self.player_token = None
        self.player_id = None
        self.admin_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.passed_tests = []

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            self.passed_tests.append(test_name)
            print(f"✅ {test_name} - PASSED")
        else:
            self.failed_tests.append({"test": test_name, "details": details})
            print(f"❌ {test_name} - FAILED: {details}")

    def make_request(self, method, endpoint, data=None, token=None, expected_status=200):
        """Make API request with proper headers"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = self.session.patch(url, json=data, headers=headers)
            else:
                return False, f"Unsupported method: {method}"

            success = response.status_code == expected_status
            if success:
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                return False, f"Status {response.status_code}: {response.text}"
        except Exception as e:
            return False, f"Request error: {str(e)}"

    def test_health_check(self):
        """Test health endpoint"""
        success, result = self.make_request('GET', 'health')
        self.log_result("Health Check", success and 'status' in result, str(result) if not success else "")

    def test_user_registration(self):
        """Test user registration with welcome bonus"""
        timestamp = int(time.time())
        test_email = f"testplayer{timestamp}@test.com"
        
        success, result = self.make_request('POST', 'auth/register', {
            "email": test_email,
            "password": "test123",
            "name": "Test Player"
        })
        
        if success and 'token' in result and result.get('balance') == 1000.0:
            self.player_token = result['token']
            self.player_id = result['id']
            self.log_result("User Registration with $1000 Welcome Bonus", True)
        else:
            self.log_result("User Registration with $1000 Welcome Bonus", False, str(result))

    def test_admin_login(self):
        """Test admin login"""
        success, result = self.make_request('POST', 'auth/login', {
            "email": "admin@casino.com",
            "password": "admin123"
        })
        
        if success and 'token' in result and result.get('role') in ['admin', 'super_admin']:
            self.admin_token = result['token']
            self.admin_id = result['id']
            self.log_result("Admin Login", True)
        else:
            self.log_result("Admin Login", False, str(result))

    def test_player_login(self):
        """Test player login with existing credentials"""
        success, result = self.make_request('POST', 'auth/login', {
            "email": "testplayer@test.com",
            "password": "test123"
        })
        
        if success and 'token' in result:
            # Use existing test player if available
            if not self.player_token:
                self.player_token = result['token']
                self.player_id = result['id']
            self.log_result("Player Login", True)
        else:
            self.log_result("Player Login", False, str(result))

    def test_auth_me(self):
        """Test authenticated user endpoint"""
        if not self.player_token:
            self.log_result("Auth Me Endpoint", False, "No player token available")
            return
            
        success, result = self.make_request('GET', 'auth/me', token=self.player_token)
        self.log_result("Auth Me Endpoint", success and 'email' in result, str(result) if not success else "")

    def test_logout(self):
        """Test logout endpoint"""
        success, result = self.make_request('POST', 'auth/logout')
        self.log_result("Logout Endpoint", success, str(result) if not success else "")

    def test_games_list(self):
        """Test games listing - should show all 18 games"""
        success, result = self.make_request('GET', 'games')
        
        if success and 'games' in result:
            games = result['games']
            expected_games = ['slots', 'blackjack', 'roulette', 'crash', 'mines', 'poker', 'craps', 
                            'sicbo', 'baccarat', 'wheel', 'dragon_tiger', 'video_poker', 'hilo', 
                            'plinko', 'lottery', 'teen_patti', 'andar_bahar', 'keno']
            
            game_ids = [g.get('game_id') for g in games]
            missing_games = [g for g in expected_games if g not in game_ids]
            
            if len(games) >= 18 and not missing_games:
                self.log_result("Games List (18 Games)", True)
            else:
                self.log_result("Games List (18 Games)", False, f"Found {len(games)} games, missing: {missing_games}")
        else:
            self.log_result("Games List (18 Games)", False, str(result))

    def test_game_play(self, game_name, bet_amount=10, params=None):
        """Test individual game play"""
        if not self.player_token:
            self.log_result(f"Play {game_name.title()}", False, "No player token available")
            return
            
        # Special handling for baccarat minimum bet
        if game_name == 'baccarat' and bet_amount < 10:
            bet_amount = 10
            
        play_data = {"bet_amount": bet_amount}
        if params:
            play_data["params"] = params
            
        success, result = self.make_request('POST', f'games/{game_name}/play', play_data, token=self.player_token)
        
        if success and 'win_amount' in result and 'balance' in result:
            self.log_result(f"Play {game_name.title()}", True)
        else:
            self.log_result(f"Play {game_name.title()}", False, str(result))

    def test_all_games(self):
        """Test all 18 casino games"""
        game_configs = {
            'slots': {},
            'blackjack': {},
            'roulette': {'bet_type': 'color', 'value': 'red'},
            'crash': {'auto_cashout': 2.0},
            'mines': {'mines_count': 3, 'tiles_revealed': 5},
            'poker': {},
            'craps': {'bet_type': 'pass'},
            'sicbo': {'bet_type': 'big'},
            'baccarat': {'bet_on': 'player'},  # Min bet $10
            'wheel': {},
            'dragon_tiger': {'bet_on': 'dragon'},
            'video_poker': {},
            'hilo': {'guess': 'higher'},
            'plinko': {'risk': 'medium'},
            'lottery': {},
            'teen_patti': {'bet_on': 'player'},
            'andar_bahar': {'bet_on': 'andar'},
            'keno': {}
        }
        
        for game_name, params in game_configs.items():
            self.test_game_play(game_name, params=params)

    def test_wallet_balance(self):
        """Test wallet balance check"""
        if not self.player_token:
            self.log_result("Check Balance", False, "No player token available")
            return
            
        success, result = self.make_request('GET', 'user/balance', token=self.player_token)
        self.log_result("Check Balance", success and 'balance' in result, str(result) if not success else "")

    def test_deposit(self):
        """Test deposit funds"""
        if not self.player_token:
            self.log_result("Deposit Funds", False, "No player token available")
            return
            
        success, result = self.make_request('POST', 'user/deposit', {"amount": 100.0}, token=self.player_token)
        self.log_result("Deposit Funds", success and 'balance' in result, str(result) if not success else "")

    def test_withdraw_insufficient(self):
        """Test withdraw with insufficient balance"""
        if not self.player_token:
            self.log_result("Withdraw Insufficient Balance Error", False, "No player token available")
            return
            
        success, result = self.make_request('POST', 'user/withdraw', {"amount": 999999.0}, token=self.player_token, expected_status=400)
        self.log_result("Withdraw Insufficient Balance Error", success, str(result) if not success else "")

    def test_withdraw_valid(self):
        """Test valid withdrawal"""
        if not self.player_token:
            self.log_result("Valid Withdrawal", False, "No player token available")
            return
            
        success, result = self.make_request('POST', 'user/withdraw', {"amount": 50.0}, token=self.player_token)
        self.log_result("Valid Withdrawal", success and 'balance' in result, str(result) if not success else "")

    def test_transaction_history(self):
        """Test transaction history"""
        if not self.player_token:
            self.log_result("Transaction History", False, "No player token available")
            return
            
        success, result = self.make_request('GET', 'user/transactions', token=self.player_token)
        self.log_result("Transaction History", success and 'transactions' in result, str(result) if not success else "")

    def test_bet_history(self):
        """Test bet history"""
        if not self.player_token:
            self.log_result("Bet History", False, "No player token available")
            return
            
        success, result = self.make_request('GET', 'user/bets', token=self.player_token)
        self.log_result("Bet History", success and 'bets' in result, str(result) if not success else "")

    def test_admin_dashboard(self):
        """Test admin dashboard"""
        if not self.admin_token:
            self.log_result("Admin Dashboard", False, "No admin token available")
            return
            
        success, result = self.make_request('GET', 'admin/dashboard', token=self.admin_token)
        expected_fields = ['total_users', 'active_users', 'total_bets', 'total_wagered', 'ggr']
        
        if success and all(field in result for field in expected_fields):
            self.log_result("Admin Dashboard", True)
        else:
            self.log_result("Admin Dashboard", False, str(result))

    def test_admin_users_list(self):
        """Test admin users list"""
        if not self.admin_token:
            self.log_result("Admin Users List", False, "No admin token available")
            return
            
        success, result = self.make_request('GET', 'admin/users', token=self.admin_token)
        self.log_result("Admin Users List", success and 'users' in result, str(result) if not success else "")

    def test_admin_adjust_balance(self):
        """Test admin balance adjustment"""
        if not self.admin_token or not self.player_id:
            self.log_result("Admin Adjust Balance", False, "No admin token or player ID available")
            return
            
        success, result = self.make_request('PATCH', f'admin/users/{self.player_id}/balance', 
                                          {"amount": 100.0, "reason": "Test adjustment"}, token=self.admin_token)
        self.log_result("Admin Adjust Balance", success and 'balance' in result, str(result) if not success else "")

    def test_admin_user_status(self):
        """Test admin user status change"""
        if not self.admin_token or not self.player_id:
            self.log_result("Admin User Status Change", False, "No admin token or player ID available")
            return
            
        # Freeze user
        success, result = self.make_request('PATCH', f'admin/users/{self.player_id}/status', 
                                          {"status": "frozen", "reason": "Test freeze"}, token=self.admin_token)
        
        if success:
            # Reactivate user
            success2, result2 = self.make_request('PATCH', f'admin/users/{self.player_id}/status', 
                                                {"status": "active", "reason": "Test reactivate"}, token=self.admin_token)
            self.log_result("Admin User Status Change", success2, str(result2) if not success2 else "")
        else:
            self.log_result("Admin User Status Change", False, str(result))

    def test_admin_game_config(self):
        """Test admin game configuration"""
        if not self.admin_token:
            self.log_result("Admin Game Config", False, "No admin token available")
            return
            
        # Get game configs
        success, result = self.make_request('GET', 'admin/games/config', token=self.admin_token)
        
        if success and 'configs' in result and result['configs']:
            # Try to toggle a game
            game_id = result['configs'][0]['game_id']
            current_enabled = result['configs'][0]['enabled']
            
            success2, result2 = self.make_request('PATCH', f'admin/games/{game_id}/config', 
                                                {"enabled": not current_enabled}, token=self.admin_token)
            self.log_result("Admin Game Config", success2, str(result2) if not success2 else "")
        else:
            self.log_result("Admin Game Config", False, str(result))

    def test_admin_pnl_report(self):
        """Test admin P&L report"""
        if not self.admin_token:
            self.log_result("Admin P&L Report", False, "No admin token available")
            return
            
        success, result = self.make_request('GET', 'admin/reports/pnl', token=self.admin_token)
        expected_fields = ['total_wagered', 'total_paid', 'ggr', 'hold_pct']
        
        if success and all(field in result for field in expected_fields):
            self.log_result("Admin P&L Report", True)
        else:
            self.log_result("Admin P&L Report", False, str(result))

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🎰 Starting Casino Platform API Testing...")
        print("=" * 60)
        
        # Health and basic tests
        self.test_health_check()
        
        # Authentication tests
        self.test_user_registration()
        self.test_admin_login()
        self.test_player_login()  # Fallback if registration failed
        self.test_auth_me()
        self.test_logout()
        
        # Game tests
        self.test_games_list()
        self.test_all_games()
        
        # Wallet tests
        self.test_wallet_balance()
        self.test_deposit()
        self.test_withdraw_insufficient()
        self.test_withdraw_valid()
        self.test_transaction_history()
        self.test_bet_history()
        
        # Admin tests
        self.test_admin_dashboard()
        self.test_admin_users_list()
        self.test_admin_adjust_balance()
        self.test_admin_user_status()
        self.test_admin_game_config()
        self.test_admin_pnl_report()
        
        # Print results
        print("\n" + "=" * 60)
        print(f"🎯 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests ({len(self.failed_tests)}):")
            for test in self.failed_tests:
                print(f"  • {test['test']}: {test['details']}")
        
        if self.passed_tests:
            print(f"\n✅ Passed Tests ({len(self.passed_tests)}):")
            for test in self.passed_tests[:10]:  # Show first 10
                print(f"  • {test}")
            if len(self.passed_tests) > 10:
                print(f"  • ... and {len(self.passed_tests) - 10} more")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n📊 Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = CasinoAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())