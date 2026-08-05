# RMR (Riders Made Riches) - Product Requirements Document

## Original Problem Statement
Build a fully functioning, ready-to-launch ride-to-earn app called RMR (Riders Made Riches). The app tracks rides, rewards users with Solana-based RMR tokens, includes a P2P marketplace, airdrops, challenges, and leaderboards. The UI should match a cyberpunk/futuristic aesthetic from the user's Replit project (Orbitron/Rajdhani fonts, Electric Blue/Hot Pink/Gold neon colors, dark backgrounds).

## Tech Stack
- **Frontend**: React 18 + Tailwind CSS + Shadcn/UI + Framer Motion
- **Backend**: FastAPI + Python
- **Database**: MongoDB
- **Auth**: Emergent-managed Google OAuth
- **Maps**: Mapbox GL JS (dark-v11 theme)
- **Payments**: Stripe (test mode)
- **Crypto**: Solana SPL Tokens (demo mode - awaiting valid secret key)
- **Storage**: Emergent Object Storage (P2P listing images)
- **Video**: Sora 2 (action rider videos)

## Core Features (Implemented)
1. **Google Auth** - Emergent-managed OAuth login + in-app browser detector
2. **Dashboard** - Bento grid with RMR balance (gold neon), Level/XP, Rank, Distance, Rides, Vehicle
3. **Ride Tracking** - GPS-validated ride tracking with Mapbox dark map, speedometer overlay, distance/duration/speed stats
4. **Airdrops** - Location-based RMR airdrops with map visualization
5. **Challenges** - Join/complete challenges with progress tracking, cinematic video completion screens
6. **Marketplace/Shop** - 88+ products across 14 categories with AI dropship agent, Official shop + P2P listings
7. **Wallet** - RMR balance, Stripe token purchases, Solana wallet linking, on-chain minting (demo)
8. **Leaderboard** - Podium with neon gold/pink styling, full rider rankings
9. **Profile** - Edit profile, change vehicle type
10. **Admin Dashboard** - 6 tabs: Users (paginated search), RMR (mint/burn), Items, Quests, Audit Log, Dropship Agent
11. **Video Preview** - 6 Sora 2-generated action rider videos
12. **Cinematic Splash Screen** - Video background intro on landing page
13. **Speedometer** - SVG neon gauge on ride tracking map
14. **Challenge Completion Screen** - Fullscreen cinematic video celebration with slow-mo
15. **Ride Completion Screen** - Vehicle-matched video celebration
16. **AI Dropshipping Agent** - GPT-powered product generator seeding marketplace
17. **Bootstrap Admin** - POST /api/admin/bootstrap allows first user to self-promote when no admins exist
18. **Solana Tools** - Feature-flagged on-chain SPL token minting, P2P transfers, balance checking via solana_service.py
19. **Marketplace SOL Payments** - Buy items with RMR or SOL (auto-converted at configurable rate)
20. **Wallet Transfers** - Send RMR to any Solana wallet address (P2P)
21. **Achievement NFTs** - 14 achievements across 7 categories with progress tracking, RMR rewards, on-chain NFT minting (demo/live)
22. **RMR Staking** - 3 tiers (7d/5%, 30d/12%, 90d/25% APY), early exit penalty, reward capping
23. **Auto-Admin** - First Google OAuth login auto-promoted to admin
24. **Admin Solana Setup** - One-click devnet bootstrap button in Admin Dashboard
25. **NEW: Carbon Footprint Tracker** (`/carbon`) - Personal CO₂ saved (lifetime + monthly), tree-years/car-km/phone-charge equivalents, by-vehicle breakdown
26. **NEW: Monthly Eco-Leaderboard** - Top CO₂ savers ranked, user highlighted, crown for #1
27. **NEW: Monthly Carbon Award** - Admin triggers +500 RMR airdrop (on-chain mint if wallet linked) to top eco-rider; duplicate prevention
28. **NEW: Carbon Hall of Fame** - Past monthly winners with on-chain explorer links

## UI Theme - Cyberpunk/Futuristic
- **Fonts**: Orbitron (display/headings), Rajdhani (body), Inter (sans)
- **Colors**: Electric Blue (#1E90FF), Hot Pink (#FF33CC), Gold (#FFD700), Neon Green (#00E64D), Cyan (#00BFFF)
- **Background**: Deep space black (240 10% 4%) with subtle grid pattern
- **Effects**: Neon glow text shadows, glass-morphism cards, neon borders, gradient text
- **Maps**: Mapbox dark-v11 theme

## DB Schema
- `users`: email, rmr_balance, wallet_address, role, level, xp, vehicle_type
- `rides`: user_id, distance_km, start_time, end_time, route_coordinates, rmr_earned
- `listings`: title, price, image_url, seller_id, category, condition
- `challenges`: title, category, difficulty, requirement, reward_rmr
- `airdrops`: latitude, longitude, value, radius
- `admins`: user_id, promoted_by, created_at
- `carbon_awards`: year, month, winner_user_id, saved_kg, reward_rmr, sol_signature, awarded_by

## Carbon Footprint Formula
- car_baseline = 170 g CO₂ / km
- saved_kg = (170 - vehicle_g_per_km) × distance_km / 1000
- Vehicle emissions: bicycle/skateboard = 0, ebike = 6, e-skateboard/onewheel/euc = 5, electric_dirt_bike = 12, dirt_bike (gas) = 250
- Monthly winner = highest saved_kg in current UTC month → gets +500 RMR (admin triggers, on-chain mint if wallet linked)

## API Endpoints
- `POST /api/auth/session` - Exchange OAuth session_id for session token
- `GET /api/auth/me` - Get current authenticated user
- `POST /api/auth/logout` - Logout and clear session
- `GET /api/rider/stats` - Dashboard stats
- `POST /api/rides/start` / `POST /api/rides/stop` - Ride tracking
- `GET /api/challenges` / `POST /api/challenges/{id}/join` - Challenges
- `GET /api/airdrops/nearby` / `POST /api/airdrops/{id}/claim` - Airdrops
- `GET /api/wallet/balance` / `POST /api/wallet/link` / `POST /api/solana/mint` - Wallet
- `POST /api/payments/checkout` - Stripe payments
- `POST /api/listings` - Create P2P listing with image
- `GET /api/rider/leaderboard` - Leaderboard
- `POST /api/admin/bootstrap` - First admin self-promotion (no admins exist)
- `POST /api/admin/make-admin/{user_id}` - Promote user (requires admin)
- `GET /api/admin/check` - Check if current user is admin

## Pending/Blocked
- **Solana Live Mode**: Devnet airdrop was down during setup — run `python setup_solana.py` when devnet is available to create the RMR SPL token mint and configure SOLANA_PRIVATE_KEY + RMR_MINT_ADDRESS in .env
- **Achievement NFTs**: Next phase — on-chain ride/challenge completion NFTs

## Backlog
- Run setup_solana.py to bootstrap devnet keypair + RMR mint (blocked on devnet airdrop availability)
- Achievement NFTs for completed rides/challenges
- RMR staking for bonus rewards
- Deploy to production and set up custom domain (kilovoltzemoto.com)
- Pitch deck structure / funding strategy materials
- Backend refactoring (modularize server.py into /routes)
- Social features (share rides, follow riders)
- Push notifications for nearby airdrops
- Product images for KiloVoltz & RMR brand merchandise
