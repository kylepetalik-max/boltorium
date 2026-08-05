"""
RMR (Riders Made Riches) API Tests
Tests all backend endpoints for the ride-to-earn app
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
SESSION_TOKEN = os.environ.get('RMR_TEST_SESSION_TOKEN', '')

@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture
def auth_client(api_client):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {SESSION_TOKEN}"})
    return api_client


class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_health_endpoint(self, api_client):
        """Test /api/health returns healthy status"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_auth_me_with_valid_token(self, auth_client):
        """Test /api/auth/me returns user data with valid Bearer token"""
        response = auth_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        
        assert "user_id" in data
        assert "email" in data
        assert "rmr_balance" in data
        assert "level" in data
        assert "vehicle_type" in data
        
        assert isinstance(data["rmr_balance"], (int, float))
        assert data["rmr_balance"] >= 0
    
    def test_auth_me_without_token(self, api_client):
        """Test /api/auth/me returns 401 without token"""
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
    
    def test_auth_me_with_invalid_token(self, api_client):
        """Test /api/auth/me returns 401 with invalid token"""
        api_client.headers.update({"Authorization": "Bearer invalid_token_12345"})
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401


class TestRiderEndpoints:
    """Rider stats and profile endpoint tests"""
    
    def test_rider_stats(self, auth_client):
        """Test /api/rider/stats returns rider statistics"""
        response = auth_client.get(f"{BASE_URL}/api/rider/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert "totalDistance" in data
        assert "totalRides" in data
        assert "rmrBalance" in data
        assert "rank" in data
        assert "level" in data
        assert "xp" in data
        assert "xpToNextLevel" in data
        
        assert isinstance(data["totalDistance"], (int, float))
        assert isinstance(data["totalRides"], int)
        assert isinstance(data["rmrBalance"], (int, float))
    
    def test_rider_leaderboard(self, auth_client):
        """Test /api/rider/leaderboard returns top riders"""
        response = auth_client.get(f"{BASE_URL}/api/rider/leaderboard")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            leader = data[0]
            assert "user_id" in leader
            assert "rmr_balance" in leader
    
    def test_rider_transactions(self, auth_client):
        """Test /api/rider/transactions returns user transactions"""
        response = auth_client.get(f"{BASE_URL}/api/rider/transactions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestRidesEndpoints:
    """Ride tracking endpoint tests"""
    
    def test_get_rides(self, auth_client):
        """Test /api/rides returns user's rides"""
        response = auth_client.get(f"{BASE_URL}/api/rides")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_current_ride(self, auth_client):
        """Test /api/rides/current returns current ride or null"""
        response = auth_client.get(f"{BASE_URL}/api/rides/current")
        assert response.status_code == 200


class TestChallengesEndpoints:
    """Challenges endpoint tests"""
    
    def test_get_all_challenges(self, auth_client):
        """Test /api/challenges returns available challenges"""
        response = auth_client.get(f"{BASE_URL}/api/challenges")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            challenge = data[0]
            assert "challenge_id" in challenge
            assert "title" in challenge
            assert "description" in challenge
            assert "difficulty" in challenge
            assert "reward_rmr" in challenge
            assert "requirement" in challenge
    
    def test_get_my_challenges(self, auth_client):
        """Test /api/challenges/mine returns user's joined challenges"""
        response = auth_client.get(f"{BASE_URL}/api/challenges/mine")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAirdropsEndpoints:
    """Airdrops endpoint tests"""
    
    def test_get_nearby_airdrops(self, auth_client):
        """Test /api/airdrops/nearby returns airdrops"""
        response = auth_client.get(f"{BASE_URL}/api/airdrops/nearby?lat=43.6532&lng=-79.3832")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            airdrop = data[0]
            assert "airdrop_id" in airdrop
            assert "latitude" in airdrop
            assert "longitude" in airdrop
            assert "value" in airdrop


class TestMarketplaceEndpoints:
    """Marketplace endpoint tests"""
    
    def test_get_marketplace_items(self, auth_client):
        """Test /api/marketplace/items returns shop items"""
        response = auth_client.get(f"{BASE_URL}/api/marketplace/items")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if len(data) > 0:
            item = data[0]
            assert "item_id" in item
            assert "name" in item
            assert "price_rmr" in item
            assert "category" in item
    
    def test_get_featured_items(self, auth_client):
        """Test /api/marketplace/featured returns featured items"""
        response = auth_client.get(f"{BASE_URL}/api/marketplace/featured")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_listings(self, auth_client):
        """Test /api/listings returns P2P listings"""
        response = auth_client.get(f"{BASE_URL}/api/listings")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestWalletEndpoints:
    """Wallet endpoint tests"""
    
    def test_get_wallet_info(self, auth_client):
        """Test /api/wallet/info returns token info"""
        response = auth_client.get(f"{BASE_URL}/api/wallet/info")
        assert response.status_code == 200
        data = response.json()
        
        assert "mintAddress" in data
        assert "decimals" in data
        assert "cluster" in data
        assert "tokenSymbol" in data
        assert data["tokenSymbol"] == "RMR"
    
    def test_get_wallet_balance(self, auth_client):
        """Test /api/wallet/balance returns balance info"""
        response = auth_client.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 200
        data = response.json()
        
        assert "inAppBalance" in data
        assert "onChainBalance" in data
        assert "mintingEnabled" in data


class TestPaymentsEndpoints:
    """Payments endpoint tests"""
    
    def test_get_payment_packages(self, auth_client):
        """Test /api/payments/packages returns RMR purchase packages"""
        response = auth_client.get(f"{BASE_URL}/api/payments/packages")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        package = data[0]
        assert "id" in package
        assert "rmr" in package
        assert "price_cad" in package
        assert "name" in package


class TestSolanaEndpoints:
    """Solana integration endpoint tests"""
    
    def test_solana_status(self, auth_client):
        """Test /api/solana/status returns connection status"""
        response = auth_client.get(f"{BASE_URL}/api/solana/status")
        assert response.status_code == 200
        data = response.json()
        
        assert "connected" in data
        assert "minting_enabled" in data


class TestProfileUpdate:
    """Profile update endpoint tests"""
    
    def test_update_vehicle(self, auth_client):
        """Test /api/rider/vehicle updates vehicle type"""
        response = auth_client.patch(
            f"{BASE_URL}/api/rider/vehicle",
            json={"vehicleType": "ebike"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "vehicle_type" in data
        assert data["vehicle_type"] == "ebike"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
