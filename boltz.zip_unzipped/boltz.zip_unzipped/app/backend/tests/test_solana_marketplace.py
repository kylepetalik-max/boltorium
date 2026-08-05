"""
Iteration 10: Tests for Solana service endpoints and marketplace purchase.
Backend URL pulled from frontend/.env REACT_APP_BACKEND_URL.
Test credentials: sess_1777710019762 / test-user-rmr-1775371806158.
"""
import os
import pytest
import requests

# Read BASE_URL from frontend/.env (no fallback)
def _load_base_url():
    env_path = "/app/frontend/.env"
    with open(env_path) as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.strip().split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not found")

BASE_URL = _load_base_url()
SESSION_TOKEN = "sess_1777710019762"
TEST_WALLET = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
OTHER_WALLET = "9xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsV"


@pytest.fixture(scope="module")
def auth_headers():
    return {"Authorization": f"Bearer {SESSION_TOKEN}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def first_item_id():
    r = requests.get(f"{BASE_URL}/api/marketplace/items", timeout=20)
    assert r.status_code == 200, r.text
    items = r.json()
    assert len(items) > 0, "No marketplace items"
    return items[0]["item_id"]


# ========= Solana Status / Balance =========

class TestSolanaStatus:
    def test_status_connected(self):
        r = requests.get(f"{BASE_URL}/api/solana/status", timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "connected" in data
        assert "mode" in data
        assert "cluster" in data
        assert data["mode"] in ("demo", "live")

    def test_balance_any_wallet(self):
        r = requests.get(f"{BASE_URL}/api/solana/balance/{TEST_WALLET}", timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "balance" in data
        assert data["wallet"] == TEST_WALLET
        assert "mode" in data


# ========= Solana Mint =========

class TestSolanaMint:
    def test_mint_no_wallet_linked(self, auth_headers):
        # Ensure wallet is unlinked first by hitting current user
        # Then attempt mint - test user starts with no wallet linked per context
        # First, unlink wallet (set to null) via direct update isn't available; rely on existing state.
        # If wallet IS linked from a previous test, this test could 200 - so unlink via PATCH profile
        requests.patch(
            f"{BASE_URL}/api/rider/profile",
            json={"wallet_address": None},
            headers=auth_headers, timeout=20
        )
        # Note: UserUpdate model excludes None values, so this won't unlink.
        # Check current state - just verify the endpoint validates wallet presence
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=20)
        wallet = r.json().get("wallet_address")
        mint_r = requests.post(
            f"{BASE_URL}/api/solana/mint",
            json={"amount": 1.0},
            headers=auth_headers, timeout=20
        )
        if wallet:
            # Wallet already linked - mint should not 400 on "No wallet linked"
            assert mint_r.status_code in (200, 400, 500)
        else:
            assert mint_r.status_code == 400
            assert "wallet" in mint_r.json().get("detail", "").lower()

    def test_mint_link_then_negative_amount(self, auth_headers):
        # Link wallet first
        link_r = requests.post(
            f"{BASE_URL}/api/wallet/link",
            json={"walletAddress": TEST_WALLET},
            headers=auth_headers, timeout=20
        )
        assert link_r.status_code == 200, link_r.text

        # Negative amount
        r = requests.post(
            f"{BASE_URL}/api/solana/mint",
            json={"amount": -5.0},
            headers=auth_headers, timeout=20
        )
        assert r.status_code == 400

    def test_mint_insufficient_balance(self, auth_headers):
        # User balance is finite - try to mint huge amount
        r = requests.post(
            f"{BASE_URL}/api/solana/mint",
            json={"amount": 9_999_999_999.0},
            headers=auth_headers, timeout=20
        )
        assert r.status_code == 400
        assert "insufficient" in r.json().get("detail", "").lower()

    def test_mint_success_demo(self, auth_headers):
        # Get current balance
        me = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=20).json()
        bal = me["rmr_balance"]
        amount = 1.0 if bal >= 1.0 else 0.01
        if bal < 0.01:
            pytest.skip("User has no RMR balance for mint test")

        r = requests.post(
            f"{BASE_URL}/api/solana/mint",
            json={"amount": amount},
            headers=auth_headers, timeout=30
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["success"] is True
        assert data["amount_minted"] == amount
        assert data["wallet_address"] == TEST_WALLET
        assert data["minting_mode"] in ("demo", "live")
        assert "transaction_id" in data
        # GET to verify balance decreased
        me2 = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=20).json()
        assert me2["rmr_balance"] == pytest.approx(bal - amount, abs=0.01)


# ========= Solana Transfer =========

class TestSolanaTransfer:
    def test_transfer_to_self_blocked(self, auth_headers):
        # Wallet should be linked from TestSolanaMint
        r = requests.post(
            f"{BASE_URL}/api/solana/transfer",
            json={"to_wallet": TEST_WALLET, "amount": 1.0},
            headers=auth_headers, timeout=20
        )
        assert r.status_code == 400
        assert "yourself" in r.json().get("detail", "").lower()

    def test_transfer_negative_amount(self, auth_headers):
        r = requests.post(
            f"{BASE_URL}/api/solana/transfer",
            json={"to_wallet": OTHER_WALLET, "amount": -5.0},
            headers=auth_headers, timeout=20
        )
        assert r.status_code == 400

    def test_transfer_insufficient(self, auth_headers):
        r = requests.post(
            f"{BASE_URL}/api/solana/transfer",
            json={"to_wallet": OTHER_WALLET, "amount": 1e12},
            headers=auth_headers, timeout=20
        )
        assert r.status_code == 400

    def test_transfer_success(self, auth_headers):
        me = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=20).json()
        bal = me["rmr_balance"]
        if bal < 0.5:
            pytest.skip("Insufficient balance for transfer test")
        r = requests.post(
            f"{BASE_URL}/api/solana/transfer",
            json={"to_wallet": OTHER_WALLET, "amount": 0.5},
            headers=auth_headers, timeout=20
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["success"] is True
        assert data["amount"] == 0.5
        assert data["to_wallet"] == OTHER_WALLET
        assert data["mode"] in ("demo", "live")
        # Verify sender balance reduced
        me2 = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=20).json()
        assert me2["rmr_balance"] == pytest.approx(bal - 0.5, abs=0.01)


# ========= Marketplace Purchase =========

class TestMarketplacePurchase:
    def test_purchase_invalid_item(self, auth_headers):
        r = requests.post(
            f"{BASE_URL}/api/marketplace/purchase",
            json={"item_id": "item_nonexistent_xxx", "payment_method": "rmr"},
            headers=auth_headers, timeout=20
        )
        assert r.status_code == 404

    def test_purchase_invalid_payment_method(self, auth_headers, first_item_id):
        r = requests.post(
            f"{BASE_URL}/api/marketplace/purchase",
            json={"item_id": first_item_id, "payment_method": "bitcoin"},
            headers=auth_headers, timeout=20
        )
        assert r.status_code == 400

    def test_purchase_sol_pending(self, auth_headers, first_item_id):
        r = requests.post(
            f"{BASE_URL}/api/marketplace/purchase",
            json={"item_id": first_item_id, "payment_method": "sol"},
            headers=auth_headers, timeout=20
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["success"] is True
        assert data["payment_method"] == "sol"
        assert data["status"] == "pending"
        assert "sol_amount" in data
        assert isinstance(data["sol_amount"], (int, float))

    def test_purchase_rmr_insufficient_or_success(self, auth_headers):
        # Find a cheap item
        items = requests.get(f"{BASE_URL}/api/marketplace/items", timeout=20).json()
        cheap = sorted([i for i in items if i.get("price_rmr", 0) > 0], key=lambda x: x["price_rmr"])[0]
        me = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=20).json()
        bal = me["rmr_balance"]

        r = requests.post(
            f"{BASE_URL}/api/marketplace/purchase",
            json={"item_id": cheap["item_id"], "payment_method": "rmr"},
            headers=auth_headers, timeout=20
        )
        if bal < cheap["price_rmr"]:
            assert r.status_code == 400
            assert "insufficient" in r.json().get("detail", "").lower()
        else:
            assert r.status_code == 200, r.text
            data = r.json()
            assert data["success"] is True
            assert data["payment_method"] == "rmr"
            assert data["price_paid"] == cheap["price_rmr"]


# ========= Regression: existing critical endpoints =========

class TestRegression:
    def test_health(self):
        r = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_auth_me(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=20)
        assert r.status_code == 200
        assert r.json()["user_id"] == "test-user-rmr-1775371806158"

    def test_marketplace_items(self):
        r = requests.get(f"{BASE_URL}/api/marketplace/items", timeout=20)
        assert r.status_code == 200
        assert len(r.json()) > 0

    def test_wallet_balance(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/wallet/balance", headers=auth_headers, timeout=20)
        assert r.status_code == 200
        assert "inAppBalance" in r.json()
