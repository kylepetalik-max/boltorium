"""
RMR Admin API Tests - Iteration 8
Tests for admin endpoints: users, RMR supply, transactions, mint/burn, dropship agent
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
SESSION_TOKEN = os.environ.get('RMR_TEST_SESSION_TOKEN', '')
TEST_USER_ID = os.environ.get('RMR_TEST_USER_ID', '')

@pytest.fixture
def auth_headers():
    """Auth headers with session token"""
    return {"Authorization": f"Bearer {SESSION_TOKEN}", "Content-Type": "application/json"}

@pytest.fixture
def api_client():
    """Requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestMarketplaceItems:
    """Test marketplace items endpoint - should return 80+ products"""
    
    def test_marketplace_items_count(self, api_client):
        """GET /api/marketplace/items returns 80+ products including AI-generated dropship products"""
        response = api_client.get(f"{BASE_URL}/api/marketplace/items")
        assert response.status_code == 200
        items = response.json()
        assert isinstance(items, list)
        assert len(items) >= 80, f"Expected 80+ items, got {len(items)}"
        
        dropship_items = [i for i in items if i.get('source') == 'dropship_agent']
        assert len(dropship_items) > 0
        
    def test_marketplace_item_structure(self, api_client):
        """Verify item structure has required fields"""
        response = api_client.get(f"{BASE_URL}/api/marketplace/items")
        assert response.status_code == 200
        items = response.json()
        
        if items:
            item = items[0]
            required_fields = ['item_id', 'name', 'category', 'price_rmr', 'is_available']
            for field in required_fields:
                assert field in item, f"Missing field: {field}"


class TestAdminCheck:
    """Test admin check endpoint"""
    
    def test_admin_check_authenticated(self, api_client, auth_headers):
        """GET /api/admin/check returns isAdmin status"""
        response = api_client.get(f"{BASE_URL}/api/admin/check", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "isAdmin" in data
        assert data["isAdmin"], "Test user should be admin"
        
    def test_admin_check_unauthenticated(self, api_client):
        """GET /api/admin/check returns 401 without auth"""
        response = api_client.get(f"{BASE_URL}/api/admin/check")
        assert response.status_code == 401


class TestAdminUsers:
    """Test admin users endpoint"""
    
    def test_admin_users_paginated(self, api_client, auth_headers):
        """GET /api/admin/users returns paginated user list"""
        response = api_client.get(f"{BASE_URL}/api/admin/users?page=1&limit=20", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "pages" in data
        
        assert isinstance(data["users"], list)
        assert data["page"] == 1
        assert data["limit"] == 20
        
    def test_admin_users_search(self, api_client, auth_headers):
        """GET /api/admin/users with search parameter"""
        response = api_client.get(f"{BASE_URL}/api/admin/users?page=1&limit=20&search=test", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        
    def test_admin_users_unauthorized(self, api_client):
        """GET /api/admin/users returns 401 without auth"""
        response = api_client.get(f"{BASE_URL}/api/admin/users?page=1&limit=20")
        assert response.status_code == 401


class TestAdminRMRSupply:
    """Test admin RMR supply endpoint"""
    
    def test_rmr_supply(self, api_client, auth_headers):
        """GET /api/admin/rmr-supply returns circulating, minted, burned, earned totals"""
        response = api_client.get(f"{BASE_URL}/api/admin/rmr-supply", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ['totalCirculating', 'totalMinted', 'totalBurned', 'totalEarned']
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
            assert isinstance(data[field], (int, float)), f"{field} should be numeric"


class TestAdminTransactions:
    """Test admin transactions audit log endpoint"""
    
    def test_transactions_paginated(self, api_client, auth_headers):
        """GET /api/admin/transactions returns audit log with pagination"""
        response = api_client.get(f"{BASE_URL}/api/admin/transactions?page=1&limit=50", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "transactions" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data


class TestAdminMintBurn:
    """Test admin mint and burn RMR endpoints"""
    
    def test_mint_rmr(self, api_client, auth_headers):
        """POST /api/admin/mint-rmr mints RMR to a user"""
        payload = {
            "user_id": TEST_USER_ID,
            "amount": 10,
            "reason": "test_mint"
        }
        response = api_client.post(f"{BASE_URL}/api/admin/mint-rmr", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success")
        assert data.get("amount") == 10
        assert "new_balance" in data
        
    def test_burn_rmr(self, api_client, auth_headers):
        """POST /api/admin/burn-rmr burns RMR from a user"""
        payload = {
            "user_id": TEST_USER_ID,
            "amount": 5,
            "reason": "test_burn"
        }
        response = api_client.post(f"{BASE_URL}/api/admin/burn-rmr", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success")
        assert data.get("amount") == 5
        assert "new_balance" in data
        
    def test_mint_invalid_amount(self, api_client, auth_headers):
        """POST /api/admin/mint-rmr with invalid amount returns 400"""
        payload = {
            "user_id": TEST_USER_ID,
            "amount": -10,
            "reason": "test"
        }
        response = api_client.post(f"{BASE_URL}/api/admin/mint-rmr", json=payload, headers=auth_headers)
        assert response.status_code == 400


class TestAdminDropshipAgent:
    """Test admin dropship agent endpoints"""
    
    def test_dropship_status(self, api_client, auth_headers):
        """GET /api/admin/dropship-status returns product count"""
        response = api_client.get(f"{BASE_URL}/api/admin/dropship-status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "total_dropship_products" in data
        assert "status" in data
        assert data["total_dropship_products"] >= 80, f"Expected 80+ dropship products, got {data['total_dropship_products']}"


class TestAdminMakeAdmin:
    """Test admin make-admin endpoint"""
    
    def test_make_admin_already_admin(self, api_client, auth_headers):
        """POST /api/admin/make-admin/{user_id} for existing admin"""
        response = api_client.post(f"{BASE_URL}/api/admin/make-admin/{TEST_USER_ID}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "success" in data


class TestAuthEndpoints:
    """Test auth endpoints with session token"""
    
    def test_auth_me(self, api_client, auth_headers):
        """GET /api/auth/me returns user data"""
        response = api_client.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "user_id" in data
        assert "email" in data
        assert "rmr_balance" in data


class TestRiderStats:
    """Test rider stats endpoint"""
    
    def test_rider_stats(self, api_client, auth_headers):
        """GET /api/rider/stats returns rider statistics"""
        response = api_client.get(f"{BASE_URL}/api/rider/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ['totalDistance', 'totalRides', 'rmrBalance', 'rank', 'level', 'xp']
        for field in required_fields:
            assert field in data, f"Missing field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
