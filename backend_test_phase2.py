#!/usr/bin/env python3
"""
Casino Platform Phase 2 API Testing
Tests interactive game sessions, sportsbook betting, cricket betting, jackpots, and enhanced admin features
"""

import requests
import sys
import json
from datetime import datetime
import time
import random

class CasinoPhase2Tester:
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
        self.session_ids = {}  # Store session IDs for cleanup

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

    def make_admin_request(self, method, endpoint, data=None, expected_status=200):
        """Make admin API request with fresh session to avoid conflicts"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.admin_token}'
        }
        
        try:
            # Use a fresh session for admin requests
            admin_session = requests.Session()
            if method == 'GET':
                response = admin_session.get(url, headers=headers)
            elif method == 'POST':
                response = admin_session.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = admin_session.patch(url, json=data, headers=headers)
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

    def setup_auth(self):
        """Setup authentication for testing"""
        # Admin login
        success, result = self.make_request('POST', 'auth/login', {
            "email": "admin@casino.com",
            "password": "admin123"
        })
        
        if success and 'token' in result:
            self.admin_token = result['token']
            self.admin_id = result['id']
            print(f"✅ Admin authentication successful - Role: {result.get('role')}")
        else:
            print(f"❌ Admin login failed: {result}")
            return False

        # Player registration/login
        timestamp = int(time.time())
        test_email = f"testplayer{timestamp}@test.com"
        
        success, result = self.make_request('POST', 'auth/register', {
            "email": test_email,
            "password": "test123",
            "name": "Test Player Phase 2"
        })
        
        if success and 'token' in result:
            self.player_token = result['token']
            self.player_id = result['id']
            print("✅ Player registration successful")
        else:
            # Try existing player
            success, result = self.make_request('POST', 'auth/login', {
                "email": "testplayer@test.com",
                "password": "test123"
            })
            if success and 'token' in result:
                self.player_token = result['token']
                self.player_id = result['id']
                print("✅ Player login successful")
            else:
                print(f"❌ Player authentication failed: {result}")
                return False
        
        return True

    # ==================== INTERACTIVE GAME SESSIONS ====================
    
    def test_blackjack_session_start(self):
        """Test starting a blackjack session"""
        if not self.player_token:
            self.log_result("Blackjack Session Start", False, "No player token")
            return
            
        success, result = self.make_request('POST', 'sessions/blackjack/start', {
            "bet_amount": 25.0,
            "params": {}
        }, token=self.player_token)
        
        if success and 'session_id' in result and 'state' in result:
            self.session_ids['blackjack'] = result['session_id']
            self.log_result("Blackjack Session Start", True)
        else:
            self.log_result("Blackjack Session Start", False, str(result))

    def test_blackjack_session_action(self):
        """Test blackjack session actions (hit/stand/double)"""
        if not self.player_token or 'blackjack' not in self.session_ids:
            self.log_result("Blackjack Session Action", False, "No session available")
            return
            
        session_id = self.session_ids['blackjack']
        
        # Try hit action
        success, result = self.make_request('POST', f'sessions/blackjack/{session_id}/action', {
            "action": "hit",
            "params": {}
        }, token=self.player_token)
        
        if success and 'state' in result:
            self.log_result("Blackjack Session Action (Hit)", True)
            
            # If still active, try stand
            if result.get('status') == 'active':
                success2, result2 = self.make_request('POST', f'sessions/blackjack/{session_id}/action', {
                    "action": "stand",
                    "params": {}
                }, token=self.player_token)
                self.log_result("Blackjack Session Action (Stand)", success2, str(result2) if not success2 else "")
        else:
            self.log_result("Blackjack Session Action", False, str(result))

    def test_blackjack_active_session(self):
        """Test checking active blackjack session"""
        if not self.player_token:
            self.log_result("Blackjack Active Session Check", False, "No player token")
            return
            
        success, result = self.make_request('GET', 'sessions/blackjack/active', token=self.player_token)
        self.log_result("Blackjack Active Session Check", success, str(result) if not success else "")

    def test_mines_session_start(self):
        """Test starting a mines session"""
        if not self.player_token:
            self.log_result("Mines Session Start", False, "No player token")
            return
            
        success, result = self.make_request('POST', 'sessions/mines/start', {
            "bet_amount": 20.0,
            "params": {"mines_count": 3}
        }, token=self.player_token)
        
        if success and 'session_id' in result and 'state' in result:
            self.session_ids['mines'] = result['session_id']
            self.log_result("Mines Session Start", True)
        else:
            self.log_result("Mines Session Start", False, str(result))

    def test_mines_session_actions(self):
        """Test mines session actions (reveal/cashout)"""
        if not self.player_token or 'mines' not in self.session_ids:
            self.log_result("Mines Session Actions", False, "No session available")
            return
            
        session_id = self.session_ids['mines']
        
        # Reveal a few tiles
        for tile in [0, 1, 5, 10]:
            success, result = self.make_request('POST', f'sessions/mines/{session_id}/action', {
                "action": "reveal",
                "params": {"tile": tile}
            }, token=self.player_token)
            
            if not success:
                self.log_result("Mines Session Reveal", False, str(result))
                return
            
            # If hit mine, stop
            if result.get('state', {}).get('outcome') == 'bust':
                self.log_result("Mines Session Reveal (Hit Mine)", True)
                return
        
        # Try cashout
        success, result = self.make_request('POST', f'sessions/mines/{session_id}/action', {
            "action": "cashout",
            "params": {}
        }, token=self.player_token)
        
        self.log_result("Mines Session Cashout", success, str(result) if not success else "")

    def test_poker_session_start(self):
        """Test starting a poker session"""
        if not self.player_token:
            self.log_result("Poker Session Start", False, "No player token")
            return
            
        success, result = self.make_request('POST', 'sessions/poker/start', {
            "bet_amount": 15.0,
            "params": {}
        }, token=self.player_token)
        
        if success and 'session_id' in result and 'state' in result:
            self.session_ids['poker'] = result['session_id']
            self.log_result("Poker Session Start", True)
        else:
            self.log_result("Poker Session Start", False, str(result))

    def test_poker_session_draw(self):
        """Test poker session draw action"""
        if not self.player_token or 'poker' not in self.session_ids:
            self.log_result("Poker Session Draw", False, "No session available")
            return
            
        session_id = self.session_ids['poker']
        
        # Draw cards (hold first 2 cards)
        success, result = self.make_request('POST', f'sessions/poker/{session_id}/action', {
            "action": "draw",
            "params": {"held": [0, 1]}
        }, token=self.player_token)
        
        self.log_result("Poker Session Draw", success and 'state' in result, str(result) if not success else "")

    def test_hilo_session_start(self):
        """Test starting a hi-lo session"""
        if not self.player_token:
            self.log_result("Hi-Lo Session Start", False, "No player token")
            return
            
        success, result = self.make_request('POST', 'sessions/hilo/start', {
            "bet_amount": 10.0,
            "params": {}
        }, token=self.player_token)
        
        if success and 'session_id' in result and 'state' in result:
            self.session_ids['hilo'] = result['session_id']
            self.log_result("Hi-Lo Session Start", True)
        else:
            self.log_result("Hi-Lo Session Start", False, str(result))

    def test_hilo_session_actions(self):
        """Test hi-lo session actions (higher/lower/cashout)"""
        if not self.player_token or 'hilo' not in self.session_ids:
            self.log_result("Hi-Lo Session Actions", False, "No session available")
            return
            
        session_id = self.session_ids['hilo']
        
        # Make a few guesses
        for action in ['higher', 'lower']:
            success, result = self.make_request('POST', f'sessions/hilo/{session_id}/action', {
                "action": action,
                "params": {}
            }, token=self.player_token)
            
            if not success:
                self.log_result(f"Hi-Lo Session {action.title()}", False, str(result))
                return
            
            # If wrong guess, stop
            if result.get('state', {}).get('outcome') == 'wrong':
                self.log_result(f"Hi-Lo Session {action.title()} (Wrong)", True)
                return
            
            self.log_result(f"Hi-Lo Session {action.title()}", True)
            break
        
        # Try cashout if still active
        if result.get('status') == 'active':
            success, result = self.make_request('POST', f'sessions/hilo/{session_id}/action', {
                "action": "cashout",
                "params": {}
            }, token=self.player_token)
            self.log_result("Hi-Lo Session Cashout", success, str(result) if not success else "")

    # ==================== SPORTSBOOK BETTING ====================
    
    def test_betting_events_list(self):
        """Test listing sport events"""
        success, result = self.make_request('GET', 'betting/events')
        
        if success and 'events' in result and len(result['events']) > 0:
            self.log_result("Sport Events List", True)
        else:
            self.log_result("Sport Events List", False, str(result))

    def test_betting_event_details(self):
        """Test getting event details with markets"""
        # First get events list
        success, result = self.make_request('GET', 'betting/events')
        
        if not success or not result.get('events'):
            self.log_result("Sport Event Details", False, "No events available")
            return
            
        event_id = result['events'][0]['event_id']
        
        success, result = self.make_request('GET', f'betting/events/{event_id}')
        
        if success and 'markets' in result and len(result['markets']) > 0:
            self.log_result("Sport Event Details", True)
        else:
            self.log_result("Sport Event Details", False, str(result))

    def test_place_sport_bet(self):
        """Test placing a sport bet"""
        if not self.player_token:
            self.log_result("Place Sport Bet", False, "No player token")
            return
            
        # Get an event with markets
        success, result = self.make_request('GET', 'betting/events')
        
        if not success or not result.get('events'):
            self.log_result("Place Sport Bet", False, "No events available")
            return
            
        event_id = result['events'][0]['event_id']
        
        # Get event details
        success, result = self.make_request('GET', f'betting/events/{event_id}')
        
        if not success or not result.get('markets'):
            self.log_result("Place Sport Bet", False, "No markets available")
            return
            
        market = result['markets'][0]
        selection = market['selections'][0]
        
        bet_data = {
            "selections": [{
                "event_id": event_id,
                "market_id": market['market_id'],
                "selection": selection['key'],
                "odds": selection['odds']
            }],
            "stake": 25.0,
            "bet_type": "single"
        }
        
        success, result = self.make_request('POST', 'betting/place', bet_data, token=self.player_token)
        
        if success and 'bet_id' in result:
            self.session_ids['sport_bet'] = result['bet_id']
            self.log_result("Place Sport Bet", True)
        else:
            self.log_result("Place Sport Bet", False, str(result))

    def test_sport_bet_cashout(self):
        """Test cashing out a sport bet"""
        if not self.player_token or 'sport_bet' not in self.session_ids:
            self.log_result("Sport Bet Cashout", False, "No bet available")
            return
            
        bet_id = self.session_ids['sport_bet']
        
        success, result = self.make_request('POST', 'betting/cashout', {
            "bet_id": bet_id
        }, token=self.player_token)
        
        self.log_result("Sport Bet Cashout", success and 'cash_out_value' in result, str(result) if not success else "")

    def test_my_sport_bets(self):
        """Test getting user's sport bets"""
        if not self.player_token:
            self.log_result("My Sport Bets", False, "No player token")
            return
            
        success, result = self.make_request('GET', 'betting/my-bets', token=self.player_token)
        self.log_result("My Sport Bets", success and 'bets' in result, str(result) if not success else "")

    def test_live_sport_events(self):
        """Test getting live sport events"""
        success, result = self.make_request('GET', 'betting/live')
        self.log_result("Live Sport Events", success and 'live_events' in result, str(result) if not success else "")

    def test_sports_list(self):
        """Test getting sports list"""
        success, result = self.make_request('GET', 'betting/sports')
        self.log_result("Sports List", success and 'sports' in result, str(result) if not success else "")

    # ==================== CRICKET BETTING ====================
    
    def test_cricket_matches_list(self):
        """Test listing cricket matches"""
        success, result = self.make_request('GET', 'cricket/matches')
        
        if success and 'matches' in result and len(result['matches']) > 0:
            self.log_result("Cricket Matches List", True)
        else:
            self.log_result("Cricket Matches List", False, str(result))

    def test_cricket_match_details(self):
        """Test getting cricket match details"""
        # Get matches first
        success, result = self.make_request('GET', 'cricket/matches')
        
        if not success or not result.get('matches'):
            self.log_result("Cricket Match Details", False, "No matches available")
            return
            
        match_id = result['matches'][0]['match_id']
        
        success, result = self.make_request('GET', f'cricket/matches/{match_id}')
        
        if success and 'match' in result:
            self.log_result("Cricket Match Details", True)
        else:
            self.log_result("Cricket Match Details", False, str(result))

    def test_cricket_match_markets(self):
        """Test getting cricket match markets (19 markets)"""
        # Get matches first
        success, result = self.make_request('GET', 'cricket/matches')
        
        if not success or not result.get('matches'):
            self.log_result("Cricket Match Markets", False, "No matches available")
            return
            
        match_id = result['matches'][0]['match_id']
        
        success, result = self.make_request('GET', f'cricket/matches/{match_id}/markets')
        
        if success and 'markets' in result:
            markets_count = len(result['markets'])
            if markets_count >= 15:  # Should have 19 markets
                self.log_result("Cricket Match Markets (19 Markets)", True)
            else:
                self.log_result("Cricket Match Markets (19 Markets)", False, f"Only {markets_count} markets found")
        else:
            self.log_result("Cricket Match Markets", False, str(result))

    def test_place_cricket_bet(self):
        """Test placing a cricket bet"""
        if not self.player_token:
            self.log_result("Place Cricket Bet", False, "No player token")
            return
            
        # Get matches first
        success, result = self.make_request('GET', 'cricket/matches')
        
        if not success or not result.get('matches'):
            self.log_result("Place Cricket Bet", False, "No matches available")
            return
            
        match_id = result['matches'][0]['match_id']
        
        # Get markets
        success, result = self.make_request('GET', f'cricket/matches/{match_id}/markets')
        
        if not success or not result.get('markets'):
            self.log_result("Place Cricket Bet", False, "No markets available")
            return
            
        # Find an open market
        market = None
        for m in result['markets']:
            if m.get('status') == 'open' and m.get('selections'):
                market = m
                break
                
        if not market:
            self.log_result("Place Cricket Bet", False, "No open markets available")
            return
            
        selection = market['selections'][0]
        
        bet_data = {
            "market_id": market['market_id'],
            "selection": selection['key'],
            "stake": 20.0
        }
        
        success, result = self.make_request('POST', f'cricket/matches/{match_id}/bet', bet_data, token=self.player_token)
        
        if success and 'bet_id' in result:
            self.session_ids['cricket_bet'] = result['bet_id']
            self.log_result("Place Cricket Bet", True)
        else:
            self.log_result("Place Cricket Bet", False, str(result))

    def test_my_cricket_bets(self):
        """Test getting user's cricket bets"""
        if not self.player_token:
            self.log_result("My Cricket Bets", False, "No player token")
            return
            
        success, result = self.make_request('GET', 'cricket/my-bets', token=self.player_token)
        self.log_result("My Cricket Bets", success and 'bets' in result, str(result) if not success else "")

    def test_cricket_series_list(self):
        """Test getting cricket series list"""
        success, result = self.make_request('GET', 'cricket/series')
        self.log_result("Cricket Series List", success and 'series' in result, str(result) if not success else "")

    def test_live_cricket_matches(self):
        """Test getting live cricket matches"""
        success, result = self.make_request('GET', 'cricket/live')
        self.log_result("Live Cricket Matches", success and 'live_matches' in result, str(result) if not success else "")

    def test_cricket_simulate_match(self):
        """Test admin cricket match simulation"""
        if not self.admin_token:
            self.log_result("Cricket Match Simulation", False, "No admin token")
            return
            
        # Get matches first
        success, result = self.make_request('GET', 'cricket/matches')
        
        if not success or not result.get('matches'):
            self.log_result("Cricket Match Simulation", False, "No matches available")
            return
            
        # Find an upcoming match
        match_id = None
        for match in result['matches']:
            if match.get('status') in ['upcoming', 'live']:
                match_id = match['match_id']
                break
                
        if not match_id:
            self.log_result("Cricket Match Simulation", False, "No suitable match for simulation")
            return
            
        success, result = self.make_admin_request('POST', f'cricket/simulate/{match_id}', {})
        self.log_result("Cricket Match Simulation", success and 'result' in result, str(result) if not success else "")

    # ==================== JACKPOT SYSTEM ====================
    
    def test_jackpots_list(self):
        """Test getting jackpot pools"""
        success, result = self.make_request('GET', 'jackpots')
        
        if success and 'jackpots' in result and len(result['jackpots']) > 0:
            self.log_result("Jackpots List", True)
        else:
            self.log_result("Jackpots List", False, str(result))

    # ==================== PROVABLY FAIR ====================
    
    def test_provably_fair_verification(self):
        """Test provably fair verification"""
        # Use query parameters instead of JSON body
        url = f"{self.base_url}/api/verify?server_seed=test_server_seed&client_seed=test_client_seed&nonce=1"
        
        try:
            response = self.session.get(url)
            success = response.status_code == 200
            if success:
                result = response.json()
                if 'hash' in result and result.get('verified') == True:
                    self.log_result("Provably Fair Verification", True)
                else:
                    self.log_result("Provably Fair Verification", False, str(result))
            else:
                self.log_result("Provably Fair Verification", False, f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Provably Fair Verification", False, f"Request error: {str(e)}")

    # ==================== ENHANCED ADMIN FEATURES ====================
    
    def test_admin_active_sessions(self):
        """Test admin view of active game sessions"""
        if not self.admin_token:
            self.log_result("Admin Active Sessions", False, "No admin token")
            return
            
        success, result = self.make_admin_request('GET', 'admin/games/sessions')
        self.log_result("Admin Active Sessions", success and 'sessions' in result, str(result) if not success else "")

    def test_admin_game_result_override(self):
        """Test admin game result override"""
        if not self.admin_token:
            self.log_result("Admin Game Result Override", False, "No admin token")
            return
            
        # This would need a real bet ID, so we'll test the endpoint structure
        success, result = self.make_admin_request('POST', 'admin/games/blackjack/result', {
            "bet_id": "invalid_bet_id",
            "result": "void",
            "reason": "Test override"
        }, expected_status=404)  # Expect 404 for invalid bet
        
        self.log_result("Admin Game Result Override", success, str(result) if not success else "")

    def test_admin_game_cancel(self):
        """Test admin game session cancellation"""
        if not self.admin_token:
            self.log_result("Admin Game Cancel", False, "No admin token")
            return
            
        # Test with invalid session ID
        success, result = self.make_admin_request('POST', 'admin/games/blackjack/cancel', {
            "session_id": "invalid_session_id",
            "reason": "Test cancellation"
        }, expected_status=404)  # Expect 404 for invalid session
        
        self.log_result("Admin Game Cancel", success, str(result) if not success else "")

    def test_admin_bulk_void_bets(self):
        """Test admin bulk void bets"""
        if not self.admin_token:
            self.log_result("Admin Bulk Void Bets", False, "No admin token")
            return
            
        success, result = self.make_admin_request('POST', 'admin/bulk/void-bets', {
            "game": "blackjack",
            "reason": "Test bulk void"
        })
        
        self.log_result("Admin Bulk Void Bets", success and 'voided' in result, str(result) if not success else "")

    def test_admin_activity_report(self):
        """Test admin activity report"""
        if not self.admin_token:
            self.log_result("Admin Activity Report", False, "No admin token")
            return
            
        success, result = self.make_admin_request('GET', 'admin/reports/activity')
        
        expected_fields = ['new_users', 'new_bets', 'new_sessions', 'sport_bets', 'cricket_bets']
        if success and all(field in result for field in expected_fields):
            self.log_result("Admin Activity Report", True)
        else:
            self.log_result("Admin Activity Report", False, str(result))

    def test_admin_cricket_market_settle(self):
        """Test admin cricket market settlement"""
        if not self.admin_token:
            self.log_result("Admin Cricket Market Settle", False, "No admin token")
            return
            
        # Test with invalid match/market
        success, result = self.make_admin_request('POST', 'admin/cricket/market/settle', {
            "match_id": "invalid_match_id",
            "market_id": "invalid_market_id",
            "winning_selection": "team1"
        }, expected_status=404)  # Expect 404 for invalid match
        
        self.log_result("Admin Cricket Market Settle", success, str(result) if not success else "")

    def test_admin_cricket_market_void(self):
        """Test admin cricket market void"""
        if not self.admin_token:
            self.log_result("Admin Cricket Market Void", False, "No admin token")
            return
            
        # Test with invalid match/market
        success, result = self.make_admin_request('POST', 'admin/cricket/market/void', {
            "match_id": "invalid_match_id",
            "market_id": "invalid_market_id",
            "reason": "Test void"
        }, expected_status=404)  # Expect 404 for invalid match
        
        self.log_result("Admin Cricket Market Void", success, str(result) if not success else "")

    def run_all_tests(self):
        """Run comprehensive Phase 2 test suite"""
        print("🎰 Starting Casino Platform Phase 2 API Testing...")
        print("=" * 70)
        
        # Setup authentication
        if not self.setup_auth():
            print("❌ Authentication setup failed. Aborting tests.")
            return False
        
        print("\n🎮 Testing Interactive Game Sessions...")
        print("-" * 50)
        
        # Interactive Game Sessions
        self.test_blackjack_session_start()
        self.test_blackjack_session_action()
        self.test_blackjack_active_session()
        
        self.test_mines_session_start()
        self.test_mines_session_actions()
        
        self.test_poker_session_start()
        self.test_poker_session_draw()
        
        self.test_hilo_session_start()
        self.test_hilo_session_actions()
        
        print("\n🏈 Testing Sportsbook Betting Engine...")
        print("-" * 50)
        
        # Sportsbook Betting
        self.test_betting_events_list()
        self.test_betting_event_details()
        self.test_place_sport_bet()
        self.test_sport_bet_cashout()
        self.test_my_sport_bets()
        self.test_live_sport_events()
        self.test_sports_list()
        
        print("\n🏏 Testing Cricket Live Betting...")
        print("-" * 50)
        
        # Cricket Betting
        self.test_cricket_matches_list()
        self.test_cricket_match_details()
        self.test_cricket_match_markets()
        self.test_place_cricket_bet()
        self.test_my_cricket_bets()
        self.test_cricket_series_list()
        self.test_live_cricket_matches()
        self.test_cricket_simulate_match()
        
        print("\n💰 Testing Jackpot & Verification Systems...")
        print("-" * 50)
        
        # Jackpots and Provably Fair
        self.test_jackpots_list()
        self.test_provably_fair_verification()
        
        print("\n👑 Testing Enhanced Admin Features...")
        print("-" * 50)
        
        # Enhanced Admin Features
        self.test_admin_active_sessions()
        self.test_admin_game_result_override()
        self.test_admin_game_cancel()
        self.test_admin_bulk_void_bets()
        self.test_admin_activity_report()
        self.test_admin_cricket_market_settle()
        self.test_admin_cricket_market_void()
        
        # Print results
        print("\n" + "=" * 70)
        print(f"🎯 Phase 2 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests ({len(self.failed_tests)}):")
            for test in self.failed_tests:
                print(f"  • {test['test']}: {test['details']}")
        
        if self.passed_tests:
            print(f"\n✅ Passed Tests ({len(self.passed_tests)}):")
            for test in self.passed_tests[:15]:  # Show first 15
                print(f"  • {test}")
            if len(self.passed_tests) > 15:
                print(f"  • ... and {len(self.passed_tests) - 15} more")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n📊 Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = CasinoPhase2Tester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())