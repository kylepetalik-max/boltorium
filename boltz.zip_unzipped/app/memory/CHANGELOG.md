# RMR Changelog

## 2026-06-06 - Subscription Tiers + Protocol Governance
- **NEW: Three-tier membership system** (Free / Pro / VIP) with three payment methods:
  - **Pro**: $9.99 CAD/mo or 500 RMR/mo. 1.25x earning, 12% max APY, 1 governance vote, early airdrops
  - **VIP**: $29.99 CAD/mo, 2000 RMR/mo OR stake 5000+ RMR. 1.5x earning, 25% max APY, 10 governance votes, can propose, exclusive marketplace, +25% on airdrop claims
- **NEW: Protocol Governance** — VIPs propose, Pro+VIP vote. 6 proposal types: vehicle_add, vehicle_remove, parameter_change, feature_request, treasury, community. Quorum=10 voting power, threshold=60% yes. Voting power = tier base + bonus (1 per 1000 RMR staked, capped at 20).
- **NEW: Execute hooks** — Admin executes passed proposals to actually mutate the protocol. `vehicle_add` updates VEHICLE_CO2_G_PER_KM + VEHICLE_LABELS; `vehicle_remove` removes them; `parameter_change` writes to `protocol_settings` collection.
- **TIER PERKS WIRED** (subscriptions matter now):
  - `/rides/finish` applies `earn_multiplier` from user's tier → response includes `tier` + `tierMultiplier`
  - `/staking/stake` enforces `staking_apy_max` cap by tier with helpful 403 upgrade message
  - `/airdrops/{id}/claim` adds tier bonus (Pro 1.1x, VIP 1.25x) and returns `base_reward + tier_bonus`
  - `/challenges/{id}/claim` applies tier `earn_multiplier` to RMR reward
- **NEW backend endpoints**: GET /api/subscriptions/tiers, /subscriptions/me; POST /subscriptions/subscribe, /subscriptions/cancel; GET /api/governance/config, /governance/proposals, /governance/proposals/{id}, /governance/me; POST /api/governance/proposals, /governance/proposals/{id}/vote; POST /api/admin/governance/proposals/{id}/finalize, /execute
- **NEW frontend pages**: `/subscription` (3 tier cards with Stripe/RMR/stake CTAs), `/governance` (proposals list + filter chips + Create modal for VIPs), `/governance/:id` (detail with vote buttons + admin controls)
- **Profile page rebuilt** to show tier badge + 4 active perks cards (multiplier, APY cap, voting power, can propose)
- **Top nav** has new Vote link + tier crown badge on avatar + Subscription/Governance/Achievements/Admin items in profile dropdown
- **Admin Dashboard** has new Governance tab (finalize + execute + status filter)
- Test results: 95.7% (44/46) — only failures are test-state conflicts, no real bugs

## 2026-06-06 (earlier) - Billion-Dollar UI/UX Pass
- Stripped all neon graffiti / paint splatter overlays
- Rebuilt design system with restrained palette (Gold/Mint/Aurora/Violet/Rose), Space Grotesk + Inter + JetBrains Mono typography, premium glass cards, soft elevation shadows, eyebrow labels, tabular numerics
- Refined Landing (Phantom-style), Dashboard (Robinhood-style data hierarchy), Carbon (premium green hero), Layout (profile dropdown menu)

## 2026-05-17 (later) - Marketplace v2 + Auto-Award Scheduler + Admin Purge
- **Dropship Agent v2** — Completely rewrote `dropship_agent.py`. Seeded **87 realistic products** across 14 subcategories with brand-correct technical descriptions (Sur-Ron Light Bee X, Talaria Sting MX4, Segway X260, Cake Kalk OR, Stark Varg, Specialized Turbo Levo, Trek Rail, Onsra Black Carve 2, Begode EX30, Veteran Sherman-S, Fox Racing helmets, Leatt gear, etc.). USD-anchored pricing with realistic MAP ranges, auto-conversion to CAD/RMR/SOL. ~10 randomly featured.
- **Curated image bank** (`product_images.py`) — All Unsplash image URLs HTTP-verified to return 200. Deterministic hash-based picker so each product gets the same matching image on every reseed. Photos are content-accurate (motorcycles for dirt bikes, MTBs for eMTBs, e-skateboards for boards, helmets for helmets, etc.).
- **Monthly Auto-Award Scheduler** (APScheduler) — Runs at 00:05 UTC on the 1st of every month, auto-awards previous month's top eco-rider +500 RMR (mints on-chain if wallet linked). Idempotent: skips if already awarded.
- **Admin "Purge POC Users" button** (Dropship tab) — One-click cleanup of all `poc_*` seed users + their rides/transactions/sessions/awards. Useful before production launch.
- **Solana devnet airdrop** still rate-limited; demo mode continues. Re-run `setup_solana.py` when network recovers.

## 2026-05-17 - Carbon Footprint Tracker + Full Frontend Rebuild
- **NEW: Carbon Footprint page** (`/carbon`) — Tracks each rider's CO₂ saved vs driving a car. Vehicle-specific emissions (ebike=6g/km, bicycle=0g/km, dirt_bike=250g/km, etc.) vs 170g/km car baseline. Shows personal lifetime/monthly stats with tree-years, car-km offset, phone-charge equivalents. By-vehicle breakdown with progress bars.
- **NEW: Monthly Eco-Leaderboard** — Top CO₂ savers ranked monthly. Current user highlighted. Crown icon for #1.
- **NEW: Carbon Hall of Fame** — Past monthly award winners with on-chain explorer links.
- **NEW: Admin Carbon Tab** — Monthly stats, award winner button (+500 RMR airdrop, on-chain mint if wallet linked). Duplicate-award prevention.
- **NEW backend endpoints**: GET /api/carbon/me, /carbon/leaderboard, /carbon/stats, /carbon/awards; POST /api/admin/carbon/award-winner, GET /api/admin/carbon/monthly
- **NEW: Full React frontend** — Built from scratch in cyberpunk theme (Orbitron + Rajdhani fonts; Electric Blue/Hot Pink/Gold/Neon Green palette; glass-morphism cards; neon glows). 12 pages: Landing, Dashboard, Ride (Mapbox+Speedometer), Airdrops (Mapbox), Challenges, Marketplace, Wallet (Solana+Stripe+Staking), Leaderboard, Profile, Achievements, Carbon, Admin (7 tabs).
- **Fixed**: `_id` serialization bug in /api/airdrops/nearby, /api/challenges, /api/marketplace/items (insert_many was mutating dicts with ObjectId)
- **Fixed**: /api/auth/session now returns session_token in response body for bearer-token fallback in cross-domain scenarios
- **Solana**: Currently in DEMO mode because devnet airdrop is rate-limited (same as iteration 10). All flows work, signatures null. Run `setup_solana.py` when devnet recovers.
- Test results: Backend 39/41 (95.1%), Frontend 62/62 (100%), Overall 98.8%

## 2026-05-11 - Achievement NFTs, RMR Staking, Auto-Admin (Iteration 11)
- **Achievement NFTs**: 14 achievements across 7 categories (rides, distance, airdrops, challenges, marketplace, wallet, level). Progress tracking, RMR rewards on claim, NFT mint placeholder for live mode
- **RMR Staking**: 3 tiers (7d/5%APY, 30d/12%APY, 90d/25%APY). Stake/unstake with early exit 5% penalty. Reward capped at lock period. Penalty recorded as explicit transaction
- **Auto-Admin**: First Google OAuth login automatically promoted to admin (no bootstrap needed)
- **Admin Solana Tab**: Setup button to bootstrap devnet keypair + RMR mint, live Solana config status display
- **Frontend**: New Achievements page (/achievements) with NFT badge gallery, Wallet page staking section with tier selector, Admin Solana tab
- **Navigation**: Added NFTs link in top nav
- Test results: 78/78 pass (15 new + 63 regression)

## 2026-05-11 - Solana Tools & On-Chain Integration (Iteration 10)
- **Built `solana_service.py` module** — Feature-flagged Solana service: real SPL token minting, wallet-to-wallet transfers, on-chain balance checking. Demo mode when keys not configured, live mode when SOLANA_PRIVATE_KEY + RMR_MINT_ADDRESS set.
- **New endpoints**: POST /api/solana/mint (real minting), POST /api/solana/transfer (P2P transfers), GET /api/solana/balance/{wallet}, GET /api/solana/status (live devnet connection)
- **Marketplace SOL payments**: POST /api/marketplace/purchase supports payment_method "rmr" or "sol". SOL auto-converts at 1 SOL = 1000 RMR rate.
- **Frontend Wallet**: Added "Send RMR" transfer section, Solana Network status card showing connection/mode/cluster/version
- **Frontend Shop**: Added SOL price display alongside RMR price on all items
- **Re-added Solana packages** (solana, solders, base58) with lazy-load feature flag
- **Fixed SOL purchase** to also record purchase and decrement stock
- Test results: 63/63 pass (18 new Solana + 45 regression)

## 2026-04-28 - AI Dropshipping Agent & Admin Dashboard
- Built GPT-powered dropshipping agent seeding 83+ marketplace products
- Enhanced Admin Dashboard with 6 tabs (Users, RMR Supply, Items, Quests, Audit, Dropship)
- Added in-app browser detector for Google OAuth restrictions

## 2026-04-27 - Mapbox Speedometer & Video Celebrations
- Added SVG neon speedometer overlay on Ride Tracking map
- Challenge/Ride completion cinematic video modals with slow-mo
- Generated 6 Sora 2 action rider videos

## 2026-04-19 - Core App Build
- Full cyberpunk UI migration from Replit codebase
- Google Auth, Dashboard, Ride Tracking, Airdrops, Challenges
- Marketplace/Shop, Wallet (Stripe + Solana demo), Leaderboard, Profile
- Cinematic splash screen with video background
