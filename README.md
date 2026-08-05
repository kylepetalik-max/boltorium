

Boltorium — Solana Ride‑to‑Earn Mobility Engine ⚡

Boltorium is a modular, containerized ride‑to‑earn mobility system built on Solana. It provides movement validation, reward distribution, user progression, and a modern frontend for real‑time mobility tracking. The platform is optimized for high throughput, low latency, and scalable event processing.

⚙️ System Architecture

Boltorium is structured as a multi‑service application:

Frontend — React + Tailwind UI for mobility tracking, user profiles, and reward visualization.

Backend API — Node/Express service handling movement logs, validation, and reward triggers.

Solana Integration — Web3 client for signing, sending, and verifying on‑chain reward transactions.

Memory Layer — Internal docs, PRDs, and state definitions for the reward engine.

Container Environment — Remote dev environment for isolated builds and deployments.

📁 Project Structure

boltorium/
 ├── app/
 │   ├── frontend/          # React + Tailwind UI
 │   ├── backend/           # Node/Express API
 │   ├── solana/            # Web3 + on-chain logic
 │   ├── memory/            # PRD, CHANGELOG, .gitkeep
 │   └── scripts/           # DevOps, tooling, automation
 ├── docs/                  # Architecture, specs, diagrams
 └── README.md

🧩 Core Modules

Movement Engine

GPS ingestion

Movement validation

Anti‑cheat heuristics

Reward event triggers

Boltz Token Logic

Earn rate calculation

Streak multipliers

Seasonal reward modifiers

On‑chain settlement

User Progression

XP curves

Leveling

Badges

Leaderboards

🛠️ Developer Setup

Clone

git clone https://github.com/YOUR-USERNAME/boltorium.git
cd boltorium

Install

Frontend:

cd app/frontend
npm install
npm run dev

Backend:

cd app/backend
npm install
npm run dev

Solana:

cd app/solana
npm install

🔗 Environment Variables

Frontend

VITE_API_URL=http://localhost:3000

Backend

PORT=3000
SOLANA_RPC=https://api.mainnet-beta.solana.com
BOLTZ_PROGRAM_ID=<program_id>

Solana

SOLANA_RPC=https://api.mainnet-beta.solana.com
WALLET_PRIVATE_KEY=<key>

🚀 Deployment Workflow

Stage:

git add .

Commit:

git commit -m "Update module"

Push:

git push origin main

🧪 Testing

Backend:

npm run test

Solana (Anchor):

anchor test

Frontend:

npm run test

🧭 Roadmap

On‑chain movement proofs

NFT‑based rider identity

Marketplace for gear + upgrades

Global leaderboard

Mobile app (React Native)

📞 Contact

Kyle petalik

App url: boltorium.co

Kyleadmin@boltorium.coBusiness Phone: 604‑344‑0259

If you want, I can also generate a CONTRIBUTING.md, a full API reference, or a pitch‑deck‑style README depending on how you want to present Boltorium to devs or investors.