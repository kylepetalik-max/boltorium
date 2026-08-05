#!/usr/bin/env python3
"""
Comprehensive Backend Testing for RMR Subscription & Governance Features
Tests all subscription tiers, governance proposals, voting, and tier perks integration
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Backend URL from environment
BASE_URL = "https://carbon-rider-rewards.preview.emergentagent.com/api"

# Test tokens (seeded, expires 2027)
TOKENS = {
    "user_a": "poc_token_poc_user_a",  # Regular rider with wallet
    "user_b": "poc_token_poc_user_b",  # No wallet
    "admin": "poc_token_poc_admin",    # Admin
}

USER_IDS = {
    "user_a": "poc_user_a",
    "user_b": "poc_user_b",
    "admin": "poc_admin",
}


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


class RMRBackendTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failed_tests = []
        self.proposal_id = None
        self.subscription_id = None

    def log(self, message: str, color: str = Colors.RESET):
        print(f"{color}{message}{Colors.RESET}")

    def test(self, name: str, method: str, endpoint: str, expected_status: int,
             token: Optional[str] = None, data: Optional[Dict] = None,
             params: Optional[Dict] = None, validate_fn=None) -> tuple:
        """Run a single API test"""
        url = f"{BASE_URL}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        self.log(f"\n[{self.tests_run}] Testing: {name}", Colors.BLUE)
        self.log(f"    {method} {endpoint}")

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            status_match = response.status_code == expected_status
            
            if status_match:
                try:
                    response_data = response.json()
                except:
                    response_data = {}
                
                # Run custom validation if provided
                validation_passed = True
                validation_msg = ""
                if validate_fn:
                    validation_passed, validation_msg = validate_fn(response_data)
                
                if validation_passed:
                    self.tests_passed += 1
                    self.log(f"    ✅ PASSED - Status: {response.status_code}", Colors.GREEN)
                    return True, response_data
                else:
                    self.tests_failed += 1
                    self.failed_tests.append(f"{name}: {validation_msg}")
                    self.log(f"    ❌ FAILED - Validation: {validation_msg}", Colors.RED)
                    return False, response_data
            else:
                self.tests_failed += 1
                error_detail = ""
                try:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                except:
                    error_detail = response.text[:200]
                
                self.failed_tests.append(f"{name}: Expected {expected_status}, got {response.status_code} - {error_detail}")
                self.log(f"    ❌ FAILED - Expected {expected_status}, got {response.status_code}", Colors.RED)
                self.log(f"    Error: {error_detail}", Colors.RED)
                return False, {}

        except Exception as e:
            self.tests_failed += 1
            self.failed_tests.append(f"{name}: Exception - {str(e)}")
            self.log(f"    ❌ FAILED - Exception: {str(e)}", Colors.RED)
            return False, {}

    def run_all_tests(self):
        """Run all subscription and governance tests"""
        self.log("\n" + "="*80, Colors.YELLOW)
        self.log("RMR BACKEND TESTING - Subscriptions & Governance", Colors.YELLOW)
        self.log("="*80 + "\n", Colors.YELLOW)

        # ============= SUBSCRIPTION TESTS =============
        self.log("\n" + "="*80, Colors.YELLOW)
        self.log("SECTION 1: SUBSCRIPTION TIER TESTS", Colors.YELLOW)
        self.log("="*80, Colors.YELLOW)

        # Test 1: GET /api/subscriptions/tiers
        def validate_tiers(data):
            if not isinstance(data, list) or len(data) != 3:
                return False, f"Expected 3 tiers, got {len(data) if isinstance(data, list) else 'not a list'}"
            
            tier_ids = [t.get('id') for t in data]
            if set(tier_ids) != {'free', 'pro', 'vip'}:
                return False, f"Expected tiers [free, pro, vip], got {tier_ids}"
            
            # Validate tier fields
            required_fields = ['id', 'name', 'price_cad', 'price_rmr', 'min_stake_rmr', 
                             'earn_multiplier', 'staking_apy_max', 'vote_power', 'can_propose', 'features']
            for tier in data:
                for field in required_fields:
                    if field not in tier:
                        return False, f"Tier {tier.get('id')} missing field: {field}"
            
            return True, "All tiers valid"

        self.test("GET /subscriptions/tiers - List all tiers", "GET", "subscriptions/tiers", 200,
                 validate_fn=validate_tiers)

        # Test 2: GET /api/subscriptions/me (Free user)
        def validate_free_user_sub(data):
            if data.get('tier') != 'free':
                return False, f"Expected tier='free', got {data.get('tier')}"
            vp = data.get('voting_power', {})
            if vp.get('total', -1) != 0:
                return False, f"Free user should have 0 voting power, got {vp.get('total')}"
            return True, "Free user subscription valid"

        self.test("GET /subscriptions/me - Free user", "GET", "subscriptions/me", 200,
                 token=TOKENS['user_a'], validate_fn=validate_free_user_sub)

        # Test 3: Ensure user has enough RMR for testing
        self.log("\n--- Setting up test data: Ensuring user has 3000 RMR ---", Colors.YELLOW)
        # We'll try to subscribe and if it fails due to insufficient balance, we'll note it
        
        # Test 4: POST /subscriptions/subscribe - Pro tier with RMR (insufficient balance test)
        success, response = self.test("POST /subscriptions/subscribe - Pro (RMR) - Check balance", 
                                      "POST", "subscriptions/subscribe", None,
                                      token=TOKENS['user_a'],
                                      data={"tier": "pro", "payment_method": "rmr"})
        
        if not success and "Insufficient RMR" in str(response):
            self.log("    ⚠️  User needs RMR balance. This is expected if not seeded.", Colors.YELLOW)
            self.log("    Note: Manual DB setup required: db.users.update_one({user_id:'poc_user_a'},{$set:{rmr_balance:3000}})", Colors.YELLOW)
        
        # Test 5: POST /subscriptions/subscribe - Pro tier with Stripe
        def validate_stripe_checkout(data):
            if not data.get('success'):
                return False, "success field not True"
            if not data.get('checkout_url'):
                return False, "checkout_url missing"
            if not data.get('session_id'):
                return False, "session_id missing"
            if data.get('method') != 'stripe':
                return False, f"Expected method='stripe', got {data.get('method')}"
            return True, "Stripe checkout created"

        self.test("POST /subscriptions/subscribe - Pro (Stripe)", "POST", "subscriptions/subscribe", 200,
                 token=TOKENS['user_a'],
                 data={"tier": "pro", "payment_method": "stripe", 
                       "origin_url": "https://carbon-rider-rewards.preview.emergentagent.com"},
                 validate_fn=validate_stripe_checkout)

        # Test 6: POST /subscriptions/cancel - No active subscription
        self.test("POST /subscriptions/cancel - No active sub", "POST", "subscriptions/cancel", 400,
                 token=TOKENS['user_a'])

        # ============= GOVERNANCE CONFIG TESTS =============
        self.log("\n" + "="*80, Colors.YELLOW)
        self.log("SECTION 2: GOVERNANCE CONFIG TESTS", Colors.YELLOW)
        self.log("="*80, Colors.YELLOW)

        # Test 7: GET /governance/config
        def validate_gov_config(data):
            if 'proposal_types' not in data:
                return False, "proposal_types missing"
            if len(data['proposal_types']) != 6:
                return False, f"Expected 6 proposal types, got {len(data['proposal_types'])}"
            
            expected_types = {'vehicle_add', 'vehicle_remove', 'parameter_change', 
                            'feature_request', 'treasury', 'community'}
            actual_types = {pt['id'] for pt in data['proposal_types']}
            if actual_types != expected_types:
                return False, f"Proposal types mismatch. Expected {expected_types}, got {actual_types}"
            
            if data.get('quorum') != 10:
                return False, f"Expected quorum=10, got {data.get('quorum')}"
            if data.get('threshold') != 0.6:
                return False, f"Expected threshold=0.6, got {data.get('threshold')}"
            
            return True, "Governance config valid"

        self.test("GET /governance/config", "GET", "governance/config", 200,
                 validate_fn=validate_gov_config)

        # Test 8: GET /governance/proposals
        self.test("GET /governance/proposals - List all", "GET", "governance/proposals", 200,
                 token=TOKENS['user_a'])

        # Test 9: GET /governance/proposals?status=active
        self.test("GET /governance/proposals?status=active", "GET", "governance/proposals", 200,
                 token=TOKENS['user_a'], params={"status": "active"})

        # ============= GOVERNANCE PROPOSAL CREATION TESTS =============
        self.log("\n" + "="*80, Colors.YELLOW)
        self.log("SECTION 3: GOVERNANCE PROPOSAL CREATION TESTS", Colors.YELLOW)
        self.log("="*80, Colors.YELLOW)

        # Test 10: POST /governance/proposals - Free user (should fail)
        self.test("POST /governance/proposals - Free user (403)", "POST", "governance/proposals", 403,
                 token=TOKENS['user_a'],
                 data={
                     "type": "vehicle_add",
                     "title": "Add Hoverboard",
                     "description": "We should add hoverboard as a vehicle type for future riders.",
                     "duration_days": 7,
                     "metadata": {"vehicle_id": "hoverboard", "label": "Hoverboard", "g_per_km": 5}
                 })

        # Test 11: POST /governance/proposals - VIP user (need to upgrade first)
        # First, let's try to create a proposal and see if user is VIP
        # If not, we'll note that user needs to be upgraded
        
        self.log("\n--- Note: For VIP tests, user needs to be upgraded to VIP tier ---", Colors.YELLOW)
        self.log("    This requires either:", Colors.YELLOW)
        self.log("    1. Subscribing via RMR (2000 RMR)", Colors.YELLOW)
        self.log("    2. Staking 5000+ RMR (auto-promotes to VIP)", Colors.YELLOW)
        
        # ============= GOVERNANCE VOTING TESTS =============
        self.log("\n" + "="*80, Colors.YELLOW)
        self.log("SECTION 4: GOVERNANCE VOTING TESTS", Colors.YELLOW)
        self.log("="*80, Colors.YELLOW)

        # Test 12: POST /governance/proposals/{id}/vote - Free user (should fail)
        # We need a proposal ID first. Let's try to get one from the list
        success, proposals_data = self.test("GET /governance/proposals - Get for voting test", 
                                           "GET", "governance/proposals", 200,
                                           token=TOKENS['user_a'])
        
        if success and isinstance(proposals_data, list) and len(proposals_data) > 0:
            test_proposal_id = proposals_data[0].get('proposal_id')
            if test_proposal_id:
                # Test voting as free user
                self.test("POST /governance/proposals/{id}/vote - Free user (403)", 
                         "POST", f"governance/proposals/{test_proposal_id}/vote", 403,
                         token=TOKENS['user_a'],
                         data={"choice": "yes"})
        else:
            self.log("    ⚠️  No proposals found for voting tests", Colors.YELLOW)

        # Test 13: GET /governance/me
        def validate_gov_me(data):
            if 'voting_power' not in data:
                return False, "voting_power missing"
            if 'recent_votes' not in data:
                return False, "recent_votes missing"
            if 'proposed' not in data:
                return False, "proposed missing"
            return True, "Governance me data valid"

        self.test("GET /governance/me", "GET", "governance/me", 200,
                 token=TOKENS['user_a'], validate_fn=validate_gov_me)

        # ============= TIER PERK TESTS =============
        self.log("\n" + "="*80, Colors.YELLOW)
        self.log("SECTION 5: TIER PERK INTEGRATION TESTS", Colors.YELLOW)
        self.log("="*80, Colors.YELLOW)

        # Test 14: Start a ride to test tier multiplier
        success, ride_data = self.test("POST /rides/start - For tier perk test", 
                                       "POST", "rides/start", 200,
                                       token=TOKENS['user_a'],
                                       data={"vehicle_type": "ebike"})
        
        if success and ride_data.get('ride_id'):
            ride_id = ride_data['ride_id']
            
            # Test 15: Finish ride and check tier multiplier
            def validate_ride_finish(data):
                if 'tier' not in data:
                    return False, "tier field missing"
                if 'tierMultiplier' not in data:
                    return False, "tierMultiplier field missing"
                # Free user should have 1.0 multiplier
                if data.get('tier') == 'free' and data.get('tierMultiplier') != 1.0:
                    return False, f"Free user should have 1.0 multiplier, got {data.get('tierMultiplier')}"
                return True, f"Tier multiplier applied: {data.get('tierMultiplier')}x for {data.get('tier')} tier"

            self.test("POST /rides/{id}/finish - Check tier multiplier", 
                     "POST", f"rides/{ride_id}/finish", 200,
                     token=TOKENS['user_a'],
                     data={"total_distance": 5.0, "gps_trace": []},
                     validate_fn=validate_ride_finish)

        # Test 16: GET /staking/tiers
        self.test("GET /staking/tiers", "GET", "staking/tiers", 200)

        # Test 17: POST /staking/stake - 7d tier (should work for all tiers)
        # First check if user has balance
        success, user_data = self.test("GET /auth/me - Check balance for staking", 
                                       "GET", "auth/me", 200,
                                       token=TOKENS['user_a'])
        
        if success and user_data.get('rmr_balance', 0) >= 10:
            self.test("POST /staking/stake - 7d tier (Free user)", "POST", "staking/stake", 200,
                     token=TOKENS['user_a'],
                     data={"amount": 10, "tier": "7d"})
        else:
            self.log("    ⚠️  Insufficient balance for staking test", Colors.YELLOW)

        # Test 18: POST /staking/stake - 90d tier (should fail for Free user - 25% APY)
        if success and user_data.get('rmr_balance', 0) >= 100:
            self.test("POST /staking/stake - 90d tier (Free user - should fail)", 
                     "POST", "staking/stake", 403,
                     token=TOKENS['user_a'],
                     data={"amount": 100, "tier": "90d"})
        else:
            self.log("    ⚠️  Insufficient balance for 90d staking test", Colors.YELLOW)

        # Test 19: GET /auth/me - Verify bearer token still works
        def validate_auth_me(data):
            if 'user_id' not in data:
                return False, "user_id missing"
            if 'email' not in data:
                return False, "email missing"
            return True, "Auth me valid"

        self.test("GET /auth/me - Bearer token", "GET", "auth/me", 200,
                 token=TOKENS['user_a'], validate_fn=validate_auth_me)

        # ============= ADMIN TESTS =============
        self.log("\n" + "="*80, Colors.YELLOW)
        self.log("SECTION 6: ADMIN GOVERNANCE TESTS", Colors.YELLOW)
        self.log("="*80, Colors.YELLOW)

        # Test 20: Admin finalize proposal (need a proposal first)
        if success and isinstance(proposals_data, list) and len(proposals_data) > 0:
            test_proposal_id = proposals_data[0].get('proposal_id')
            if test_proposal_id:
                self.test("POST /admin/governance/proposals/{id}/finalize", 
                         "POST", f"admin/governance/proposals/{test_proposal_id}/finalize", 200,
                         token=TOKENS['admin'])

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*80, Colors.YELLOW)
        self.log("TEST SUMMARY", Colors.YELLOW)
        self.log("="*80, Colors.YELLOW)
        
        total = self.tests_run
        passed = self.tests_passed
        failed = self.tests_failed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        self.log(f"\nTotal Tests: {total}", Colors.BLUE)
        self.log(f"Passed: {passed}", Colors.GREEN)
        self.log(f"Failed: {failed}", Colors.RED)
        self.log(f"Pass Rate: {pass_rate:.1f}%", Colors.YELLOW)
        
        if self.failed_tests:
            self.log("\n" + "="*80, Colors.RED)
            self.log("FAILED TESTS:", Colors.RED)
            self.log("="*80, Colors.RED)
            for i, failure in enumerate(self.failed_tests, 1):
                self.log(f"{i}. {failure}", Colors.RED)
        
        self.log("\n" + "="*80, Colors.YELLOW)
        self.log("NOTES:", Colors.YELLOW)
        self.log("="*80, Colors.YELLOW)
        self.log("1. POC tokens must be seeded in database with expires_at in 2027", Colors.YELLOW)
        self.log("2. For full testing, ensure poc_user_a has rmr_balance >= 3000", Colors.YELLOW)
        self.log("3. For VIP tests, user needs to subscribe or stake 5000+ RMR", Colors.YELLOW)
        self.log("4. Stripe is in TEST mode - checkout URLs are real but don't complete payment", Colors.YELLOW)
        self.log("5. Some tests may fail if database is not properly seeded", Colors.YELLOW)
        
        return 0 if failed == 0 else 1


def main():
    tester = RMRBackendTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
