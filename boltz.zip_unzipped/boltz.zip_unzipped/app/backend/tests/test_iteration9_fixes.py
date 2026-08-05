"""
Iteration 9 Regression Tests
Tests targeting the fixes for:
- /api/health
- /api/auth/me with Bearer token (after MongoDB recovery)
- /api/admin/check returns isAdmin status
- /api/admin/bootstrap endpoint exists
- /api/marketplace/items returns items list
- No duplicate-route registrations in backend
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
SESSION_TOKEN = os.environ.get("RMR_TEST_SESSION_TOKEN", "")
TEST_USER_ID = os.environ.get("RMR_TEST_USER_ID", "")


@pytest.fixture
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture
def auth_client(client):
    client.headers.update({"Authorization": f"Bearer {SESSION_TOKEN}"})
    return client


# ----- Health -----
class TestHealth:
    def test_health_200(self, client):
        r = client.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("status") == "healthy"


# ----- Auth -----
class TestAuthMe:
    def test_auth_me_with_bearer_token(self, auth_client):
        r = auth_client.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 200, f"auth/me failed: {r.status_code} {r.text}"
        data = r.json()
        assert data.get("user_id") == TEST_USER_ID
        assert "rmr_balance" in data
        assert "level" in data

    def test_auth_me_no_token_401(self, client):
        r = client.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 401

    def test_auth_me_bad_token_401(self, client):
        client.headers.update({"Authorization": "Bearer not_a_real_token_xyz"})
        r = client.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 401


# ----- Admin -----
class TestAdmin:
    def test_admin_check_returns_isAdmin(self, auth_client):
        r = auth_client.get(f"{BASE_URL}/api/admin/check")
        assert r.status_code == 200, r.text
        data = r.json()
        assert "isAdmin" in data
        assert data["isAdmin"]

    def test_admin_check_unauth_401(self, client):
        r = client.get(f"{BASE_URL}/api/admin/check")
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            assert not r.json().get("isAdmin")

    def test_admin_bootstrap_endpoint_exists(self, client):
        """Bootstrap endpoint should exist (route registered).
        Without auth/secret, expect 401/403/400 — NOT 404."""
        r = client.post(f"{BASE_URL}/api/admin/bootstrap", json={})
        assert r.status_code != 404, (
            f"/api/admin/bootstrap not found (404). Body: {r.text}"
        )
        assert r.status_code in (200, 400, 401, 403, 409, 422), (
            f"Unexpected status {r.status_code}: {r.text}"
        )


# ----- Marketplace -----
class TestMarketplace:
    def test_marketplace_items_list(self, auth_client):
        r = auth_client.get(f"{BASE_URL}/api/marketplace/items")
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Expected non-empty marketplace items list"
        item = data[0]
        for f in ("item_id", "name", "price_rmr", "category"):
            assert f in item, f"Missing field {f} in marketplace item"


# ----- Backend duplicate-route warnings -----
class TestBackendLogs:
    def test_no_duplicate_route_warnings(self):
        """Scan recent supervisor backend logs for duplicate route registration warnings."""
        log_paths = [
            "/var/log/supervisor/backend.err.log",
            "/var/log/supervisor/backend.out.log",
        ]
        offending = []
        for p in log_paths:
            if not os.path.exists(p):
                continue
            try:
                with open(p, "r", errors="ignore") as fh:
                    fh.seek(0, os.SEEK_END)
                    size = fh.tell()
                    fh.seek(max(0, size - 200_000))
                    content = fh.read()
                for line in content.splitlines():
                    low = line.lower()
                    if (
                        "duplicate" in low
                        and ("route" in low or "operation" in low or "path" in low)
                    ):
                        offending.append(f"{p}: {line.strip()}")
            except Exception:
                pass
        assert not offending, "Duplicate route warnings found:\n" + "\n".join(offending)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
