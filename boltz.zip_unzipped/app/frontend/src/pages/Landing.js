import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useEffect } from 'react';
import {
  Bike, Coins, Trophy, Gift, Target, Leaf, Wallet as WalletIcon,
  Sparkles, Zap, Shield, MapPin, ArrowUpRight, CheckCircle2
} from 'lucide-react';

const FEATURES = [
  { id: 'ride',       icon: Bike,       title: 'Ride to Earn',         desc: 'Track GPS rides on any LEV. Get VOLTZ per kilometer.',         color: 'text-accent-aurora' },
  { id: 'airdrops',   icon: Gift,       title: 'Geo Airdrops',         desc: 'Hunt VOLTZ drops placed in the real world.',                   color: 'text-accent-rose' },
  { id: 'challenges', icon: Target,     title: 'Quests & Levels',      desc: 'Complete missions, level up, unlock multipliers.',           color: 'text-accent-gold' },
  { id: 'carbon',     icon: Leaf,       title: 'Carbon Footprint',     desc: 'Save CO₂. Top eco-rider wins a monthly VOLTZ airdrop.',        color: 'text-accent-mint' },
  { id: 'solana',     icon: Coins,      title: 'Solana On-Chain',      desc: 'VOLTZ is a real SPL token. Withdraw to any wallet.',           color: 'text-accent-violet' },
  { id: 'shop',       icon: Trophy,     title: 'Marketplace',          desc: 'Spend VOLTZ or SOL on real e-mobility gear.',                  color: 'text-accent-aurora' },
];

export default function Landing() {
  const { user, login, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => { if (!loading && user) navigate('/dashboard'); }, [loading, user, navigate]);

  return (
    <div className="min-h-screen relative">
      {/* Top bar */}
      <header className="sticky top-0 z-30 glass-strong border-b border-white/[0.06]">
        <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center font-display font-bold text-base" style={{ background: 'linear-gradient(135deg, #F5C842 0%, #E8A700 100%)', color: '#1a1100', boxShadow: '0 0 0 1px rgba(255,255,255,0.1) inset, 0 8px 20px -8px rgba(245,200,66,0.5)' }}>R</div>
            <div className="hidden sm:block leading-tight">
              <div className="font-display font-bold text-[15px] tracking-tight">RMR</div>
              <div className="text-[10px] tracking-[0.18em] text-white/45 uppercase font-mono">Ride to Earn</div>
            </div>
          </div>
          <button onClick={login} className="btn btn-primary" data-testid="landing-login-top">
            Sign in with Google <ArrowUpRight size={14} />
          </button>
        </div>
      </header>

      {/* Hero */}
      <section className="relative pt-20 pb-28 px-4 sm:px-6 lg:px-8 z-10 overflow-hidden">
        {/* subtle glow blob behind hero */}
        <div className="absolute left-1/2 -translate-x-1/2 top-0 w-[920px] h-[920px] -z-0" style={{ background: 'radial-gradient(ellipse 50% 40% at 50% 30%, rgba(245,200,66,0.13), transparent 60%)' }} />
        <div className="max-w-5xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full glass mb-7" data-testid="hero-badge">
            <span className="pulse-dot" />
            <span className="text-[11px] font-mono tracking-[0.18em] text-white/75 uppercase">Solana Devnet — Live</span>
          </div>
          <h1 className="font-display font-bold text-[3rem] sm:text-[4.5rem] lg:text-[5.5rem] leading-[1.02] tracking-[-0.04em] text-balance">
            <span className="grad-headline">The ride-to-earn</span><br/>
            <span className="grad-gold">protocol for riders.</span>
          </h1>
          <p className="mt-7 max-w-2xl mx-auto text-[17px] sm:text-lg text-white/65 leading-relaxed">
            Track every kilometer on your e-bike, EUC, skate or onewheel. Mint <span className="text-accent-gold font-medium">VOLTZ</span> tokens on Solana, hunt geo-airdrops, save the planet, and trade for real gear.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row gap-3 justify-center items-center">
            <button onClick={login} className="btn btn-primary btn-lg" data-testid="landing-login-hero">
              <Zap size={16} /> Start earning — free
            </button>
            <a href="#features" className="btn btn-ghost btn-lg">Explore the protocol</a>
          </div>
          <div className="mt-7 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-[12px] text-white/45">
            <span className="inline-flex items-center gap-1.5"><CheckCircle2 size={12} className="text-accent-mint"/> 100 VOLTZ welcome</span>
            <span className="inline-flex items-center gap-1.5"><CheckCircle2 size={12} className="text-accent-mint"/> No wallet needed to start</span>
            <span className="inline-flex items-center gap-1.5"><CheckCircle2 size={12} className="text-accent-mint"/> Free to use</span>
          </div>

          {/* Metrics */}
          <div className="mt-16 grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-3xl mx-auto">
            {[
              { label: 'Vehicle types',      value: '8' },
              { label: 'VOLTZ per km',         value: '1–1.5' },
              { label: 'CO₂ saved / 100 km', value: '~16 kg' },
              { label: 'Max staking APY',    value: '25%' },
            ].map((m) => (
              <div key={m.label} className="bento text-left">
                <div className="eyebrow mb-1">{m.label}</div>
                <div className="font-display font-bold text-2xl sm:text-[28px] tracking-tight grad-headline">{m.value}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14 max-w-2xl mx-auto">
            <div className="eyebrow mb-3">The protocol</div>
            <h2 className="font-display text-[2.25rem] sm:text-5xl font-bold tracking-[-0.03em] grad-headline">Everything real riders need</h2>
            <p className="text-white/55 mt-3 text-[15px]">Built end-to-end: GPS rides, on-chain rewards, airdrops, quests, staking, NFTs, marketplace and a carbon leaderboard.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map((f) => {
              const Icon = f.icon;
              return (
                <div key={f.id} className="bento group" data-testid={`feature-${f.id}`}>
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 bg-white/[0.04] border border-white/[0.06] ${f.color}`}>
                    <Icon size={20} strokeWidth={1.8} />
                  </div>
                  <h3 className="font-display font-semibold text-[18px] tracking-tight">{f.title}</h3>
                  <p className="text-white/55 text-sm mt-1.5 leading-relaxed">{f.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <div className="eyebrow mb-3">Three steps</div>
            <h2 className="font-display text-[2.25rem] sm:text-5xl font-bold tracking-[-0.03em] grad-headline">Simple as one ride</h2>
          </div>
          <div className="grid sm:grid-cols-3 gap-4">
            {[
              { n: '01', t: 'Sign in', d: 'One click with Google. Get 100 VOLTZ welcome bonus.', i: Shield, color: 'text-accent-aurora' },
              { n: '02', t: 'Ride', d: 'Start tracking. Live GPS, speedometer, route on a map.', i: MapPin, color: 'text-accent-mint' },
              { n: '03', t: 'Earn', d: 'Stake, shop, withdraw on-chain to your Solana wallet.', i: WalletIcon, color: 'text-accent-gold' },
            ].map((s) => {
              const I = s.i;
              return (
                <div key={s.n} className="bento">
                  <div className="flex items-start justify-between">
                    <span className="font-mono text-[12px] tracking-[0.18em] text-white/40">STEP {s.n}</span>
                    <I className={s.color} size={20} strokeWidth={1.8}/>
                  </div>
                  <h4 className="mt-4 font-display font-semibold text-[18px] tracking-tight">{s.t}</h4>
                  <p className="text-white/55 text-sm mt-1.5 leading-relaxed">{s.d}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-4xl mx-auto bento ring-gold text-center py-12 px-8 relative overflow-hidden">
          <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-[600px] h-[400px]" style={{ background: 'radial-gradient(ellipse at center, rgba(245,200,66,0.18), transparent 60%)' }} />
          <div className="relative">
            <h3 className="font-display text-3xl sm:text-[2.5rem] font-bold tracking-[-0.03em] grad-headline">Plug in. Start riding.</h3>
            <p className="text-white/65 mt-3 max-w-xl mx-auto">No friction. Login with Google, link your Solana wallet whenever you want, and let your kilometers print real on-chain tokens.</p>
            <button onClick={login} className="mt-7 btn btn-primary btn-lg" data-testid="landing-login-bottom">
              Enter the protocol <ArrowUpRight size={16}/>
            </button>
          </div>
        </div>
      </section>

      <footer className="px-4 sm:px-6 lg:px-8 py-8 text-center text-white/35 text-xs relative z-10">
        © {new Date().getFullYear()} RMR Protocol — Riders Made Riches • Solana Devnet
      </footer>
    </div>
  );
}
