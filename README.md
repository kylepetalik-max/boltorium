# Boltorium (v1 — live product)

**Live product:** [https://boltorium.co](https://boltorium.co)  
**Operator:** Kyle Petalik · Powell River, BC · [kyleadmin@boltorium.co](mailto:kyleadmin@boltorium.co)

Boltorium (“Ride the Lightning”) is a **ride-to-earn** app for electrified / micromobility riders. Riders track GPS-verified rides and earn **Boltz** on **Solana**.

> This repository is the **investor index for v1**. It is **not** a full dump of production source. The live app ships from Boltorium’s production host (Emergent) onto the custom domain `boltorium.co`.

## Honest status (read this first)

| Item | Reality |
|------|---------|
| Live site | [boltorium.co](https://boltorium.co) — public marketing + in-app experience |
| Chain | **Demo / Devnet** for rewards today. Mainnet minting is **not** live. |
| Anti-cheat | Ride verification (GPS + heuristics) before Boltz credit — see Striker work below |
| Native stores | Android / Play path in progress (wrapper around the app) — not a published store listing yet |
| This GitHub repo | Pointer + investor map. No production zip dumps. |

## What v1 includes (product)

- Public landing + enter-app flow on boltorium.co  
- Wallet / Google / email demo auth  
- Ride HUD, garage (broad micromobility types), shop, rank / missions  
- Boltz balance UX tied to verified rides (demo settlement)

## Related public repos

| Repo | Role |
|------|------|
| [`boltorium-v2`](https://github.com/kylepetalik-max/boltorium-v2) | **v2 preview** — Capacitor-ready codebase + marketing shell. Isolated from live. Preview: [GitHub Pages](https://kylepetalik-max.github.io/boltorium-v2/) |
| [`boltorium-rsp`](https://github.com/kylepetalik-max/boltorium-rsp) | Ride Signal Processor — telemetry / spoof-signal prototype (WIP) |
| [`merch-line-and-tech-packs`](https://github.com/kylepetalik-max/merch-line-and-tech-packs) | Merch line sheet + draft tech packs (**draft**, not factory-ready) |

## For investors — quick links

1. **Try live v1:** https://boltorium.co  
2. **See v2 direction (preview):** https://kylepetalik-max.github.io/boltorium-v2/#/  
3. **Contact:** kyleadmin@boltorium.co  

## What we are not claiming

- No fabricated rider / volume stats in this README  
- No claim that Solana mainnet rewards are live  
- No claim that this git tree is the full production monorepo  

---

© Boltorium · Kyle Petalik
