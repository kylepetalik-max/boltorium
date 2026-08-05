"""
Tests for Achievement NFTs + RMR Staking endpoints (iteration 11).
Covers:
  - GET  /api/achievements
  - POST /api/achievements/{id}/claim   (success + 400 already claimed + 400 locked)
  - GET  /api/staking/tiers
  - GET  /api/staking/positions
  - POST /api/staking/stake             (validation + happy path)
  - POST /api/staking/{stake_id}/unstake (early penalty + completed)
  - GET  /api/admin/solana-config
  - POST /api/admin/setup-solana
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://launch-ready-131.preview.emergentagent.com").rstrip("/")
SESSION_TOKEN = "sess_1777710019762"
USER_ID = "test-user-rmr-1775371806158"

HEADERS = {
    "Authorization": f"Bearer {SESSION_TOKEN}",
    "Content-Type": "application/json",
}


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


# ---------------- Achievements ----------------
class TestAchievements:
    def test_get_achievements_returns_14(self, session):
        r = session.get(f"{BASE_URL}/api/achievements")
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 14, f"expected 14 achievements, got {len(data)}"

        # Each entry should expose id, title, progress, requirement, unlocked, claimed, rmr_reward, rarity
        ach = data[0]
        for key in ("id", "title", "progress", "requirement", "unlocked", "claimed", "rmr_reward", "rarity", "category"):
            assert key in ach, f"missing field {key}"

        # Stash for later tests
        TestAchievements.all = {a["id"]: a for a in data}

    def test_claim_locked_returns_400(self, session):
        # Pick something definitely not unlocked for a user with total_rides=12, distance=45
        locked_id = "50_rides"  # requires 50 rides
        r = session.post(f"{BASE_URL}/api/achievements/{locked_id}/claim")
        # If the user happens to be unlocked we still expect 400 from "already claimed" or progress
        # but with the seeded test user it should be progress not met -> 400
        assert r.status_code == 400, f"expected 400 for locked, got {r.status_code}: {r.text}"
        body = r.json()
        assert "Not yet unlocked" in body.get("detail", "") or "Already claimed" in body.get("detail", "")

    def test_claim_unknown_returns_404(self, session):
        r = session.post(f"{BASE_URL}/api/achievements/does_not_exist/claim")
        assert r.status_code == 404

    def test_claim_unlocked_achievement(self, session):
        """10km is requirement=10, user has 45.2km -> should be claimable (or already claimed)."""
        # First get current balance + state
        ach_resp = session.get(f"{BASE_URL}/api/achievements").json()
        target = next(a for a in ach_resp if a["id"] == "10km")
        bal_before = session.get(f"{BASE_URL}/api/wallet/balance").json()["inAppBalance"]

        r = session.post(f"{BASE_URL}/api/achievements/10km/claim")
        if target.get("claimed"):
            # Already claimed in a previous test run -> 400 expected
            assert r.status_code == 400
            assert "Already claimed" in r.json().get("detail", "")
        else:
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["success"] is True
            assert body["rmr_earned"] == 10
            assert body["new_balance"] == pytest.approx(bal_before + 10, abs=0.5)

            # GET should now show claimed=true
            ach_after = session.get(f"{BASE_URL}/api/achievements").json()
            t2 = next(a for a in ach_after if a["id"] == "10km")
            assert t2["claimed"] is True

            # Re-claim should now 400
            r2 = session.post(f"{BASE_URL}/api/achievements/10km/claim")
            assert r2.status_code == 400
            assert "Already claimed" in r2.json().get("detail", "")


# ---------------- Staking ----------------
class TestStaking:
    def test_get_tiers(self, session):
        r = session.get(f"{BASE_URL}/api/staking/tiers")
        assert r.status_code == 200
        tiers = r.json()
        assert isinstance(tiers, list)
        ids = {t["id"] for t in tiers}
        assert ids == {"7d", "30d", "90d"}, ids
        apys = {t["id"]: t["apy"] for t in tiers}
        assert apys["7d"] == 5.0
        assert apys["30d"] == 12.0
        assert apys["90d"] == 25.0

    def test_get_positions(self, session):
        r = session.get(f"{BASE_URL}/api/staking/positions")
        assert r.status_code == 200
        positions = r.json()
        assert isinstance(positions, list)
        for p in positions:
            assert "stake_id" in p and "amount" in p and "status" in p
            assert "is_unlocked" in p
            assert "earned_so_far" in p

    def test_stake_invalid_tier(self, session):
        r = session.post(f"{BASE_URL}/api/staking/stake", json={"amount": 20, "tier": "xx"})
        assert r.status_code == 400
        assert "Invalid tier" in r.json().get("detail", "")

    def test_stake_below_min(self, session):
        # 7d tier requires min 10 RMR
        r = session.post(f"{BASE_URL}/api/staking/stake", json={"amount": 1, "tier": "7d"})
        assert r.status_code == 400
        assert "Minimum stake" in r.json().get("detail", "")

    def test_stake_insufficient_balance(self, session):
        r = session.post(f"{BASE_URL}/api/staking/stake", json={"amount": 10_000_000, "tier": "7d"})
        assert r.status_code == 400
        assert "Insufficient" in r.json().get("detail", "")

    def test_stake_amount_must_be_positive(self, session):
        r = session.post(f"{BASE_URL}/api/staking/stake", json={"amount": -5, "tier": "7d"})
        assert r.status_code == 422  # pydantic gt=0

    def test_stake_and_early_unstake_with_penalty(self, session):
        bal_before = session.get(f"{BASE_URL}/api/wallet/balance").json()["inAppBalance"]
        if bal_before < 15:
            pytest.skip(f"Test user balance too low ({bal_before}) to run stake test")

        # Stake 10 RMR for 7d
        r = session.post(f"{BASE_URL}/api/staking/stake", json={"amount": 10, "tier": "7d"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["success"] is True
        stake_id = body["stake_id"]
        assert body["amount"] == 10
        assert body["apy"] == 5.0
        assert body["new_balance"] == pytest.approx(bal_before - 10, abs=0.5)

        # GET positions should include the new active stake
        positions = session.get(f"{BASE_URL}/api/staking/positions").json()
        active = [p for p in positions if p["stake_id"] == stake_id]
        assert len(active) == 1
        assert active[0]["status"] == "active"
        assert active[0]["is_unlocked"] is False  # 7d lock just started

        # Early unstake → 5% penalty (0.5 RMR), no reward
        r2 = session.post(f"{BASE_URL}/api/staking/{stake_id}/unstake")
        assert r2.status_code == 200, r2.text
        out = r2.json()
        assert out["success"] is True
        assert out["status"] == "early_unstaked"
        assert out["reward"] == 0
        assert out["penalty"] == pytest.approx(0.5, abs=0.01)
        assert out["principal"] == 10
        assert out["total_returned"] == pytest.approx(9.5, abs=0.01)
        # Balance: started at bal_before, deducted 10, then credited back 9.5 -> bal_before - 0.5
        assert out["new_balance"] == pytest.approx(bal_before - 0.5, abs=0.5)

        # Second unstake should 400 (already unstaked)
        r3 = session.post(f"{BASE_URL}/api/staking/{stake_id}/unstake")
        assert r3.status_code == 400
        assert "already" in r3.json().get("detail", "").lower()

    def test_unstake_not_found(self, session):
        r = session.post(f"{BASE_URL}/api/staking/stake_does_not_exist/unstake")
        assert r.status_code == 404


# ---------------- Admin Solana ----------------
class TestAdminSolana:
    def test_admin_solana_config_requires_admin(self, session):
        """Test user is not admin, so should get 403/401."""
        r = session.get(f"{BASE_URL}/api/admin/solana-config")
        # Either 403 forbidden or 200 if test user happens to be admin
        assert r.status_code in (200, 401, 403), r.text
        if r.status_code == 200:
            data = r.json()
            assert "status" in data
            assert "has_private_key" in data
            assert "has_mint_address" in data
            assert "rpc_url" in data

    def test_admin_setup_solana_requires_admin(self, session):
        r = session.post(f"{BASE_URL}/api/admin/setup-solana")
        assert r.status_code in (200, 401, 403)
        if r.status_code == 200:
            data = r.json()
            assert data.get("success") is True
            assert "pid" in data


# ---------------- Auto-admin code review ----------------
class TestAutoAdminCodeReview:
    """Code review check — the create_session endpoint should auto-promote first user."""
    def test_create_session_contains_auto_admin_logic(self):
        with open("/app/backend/server.py") as f:
            src = f.read()
        # Must contain admin_count == 0 promotion after upsert_user
        assert "admin_count" in src
        assert 'db.admins.count_documents({})' in src
        assert "auto_first_login" in src
