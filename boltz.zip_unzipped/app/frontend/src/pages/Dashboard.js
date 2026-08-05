import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import CountUp from '@/components/CountUp';
import {
  Coins, Zap, MapPin, Trophy, Bike, TrendingUp,
  Gift, Target, Award, Leaf, ArrowRight, Sparkles, ArrowUpRight
} from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [carbon, setCarbon] = useState(null);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [s, c, r] = await Promise.all([
          api.get('/rider/stats'),
          api.get('/carbon/me'),
          api.get('/rides'),
        ]);
        setStats(s.data); setCarbon(c.data); setRecent(r.data.slice(0, 4));
      } finally { setLoading(false); }
    })();
  }, []);

  const xpPct = stats ? Math.min(100, (stats.xp / (stats.level * 100)) * 100) : 0;
  const greet = (() => {
    const h = new Date().getHours();
    return h < 5 ? 'Late ride' : h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening';
  })();

  return (
    <div className="fade-in space-y-7">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-5">
        <div>
          <div className="eyebrow">Overview</div>
          <h1 className="font-display font-bold text-[2.25rem] sm:text-[2.75rem] mt-1.5 tracking-[-0.03em] leading-[1.05]">
            <span className="text-white/55">{greet},</span>{' '}
            <span className="grad-headline">{user?.first_name || user?.name?.split(' ')[0] || 'Rider'}</span>
          </h1>
          <p className="text-white/50 text-[14px] mt-2 inline-flex items-center gap-3">
            <span className="inline-flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-accent-gold inline-block"/> Level <span className="text-white tabular">{stats?.level ?? 1}</span></span>
            <span className="text-white/20">•</span>
            <span className="inline-flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-accent-rose inline-block"/> Rank <span className="text-white tabular">#{stats?.rank ?? '—'}</span></span>
            <span className="text-white/20">•</span>
            <span className="inline-flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-accent-aurora inline-block"/> {user?.vehicle_type || 'ebike'}</span>
          </p>
        </div>
        <Link to="/ride" className="btn btn-primary btn-lg group" data-testid="dash-start-ride">
          <Bike size={17} /> Start a ride
          <ArrowUpRight size={15} className="transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5"/>
        </Link>
      </div>

      {/* Primary metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Hero balance */}
        <div className="bento ring-gold lg:col-span-2 relative overflow-hidden" data-testid="stat-rmr">
          <div className="absolute -top-24 -right-20 w-72 h-72 rounded-full" style={{ background: 'radial-gradient(circle, rgba(245,200,66,0.18), transparent 65%)' }}/>
          <div className="relative">
            <div className="flex items-start justify-between">
              <div>
                <div className="eyebrow mb-2">VOLTZ Balance</div>
                <div className="flex items-baseline gap-2">
                  <span className="font-display font-bold text-[3.25rem] sm:text-[4rem] tracking-[-0.04em] grad-gold tabular leading-none">
                    <CountUp value={stats?.rmrBalance ?? user?.rmr_balance ?? 0} decimals={2} />
                  </span>
                  <span className="text-accent-gold/70 text-sm font-mono tracking-widest">VOLTZ</span>
                </div>
                <div className="text-[11px] text-white/45 mt-2">Solana SPL Token · 1 SOL = 1000 VOLTZ</div>
              </div>
              <Coins className="text-accent-gold/80 float-anim" size={42} strokeWidth={1.5}/>
            </div>
            <div className="flex gap-2 mt-6">
              <Link to="/wallet" className="btn btn-primary text-[12px]">Open Wallet <ArrowUpRight size={12}/></Link>
              <Link to="/marketplace" className="btn text-[12px]">Shop →</Link>
              <Link to="/wallet#stake" className="btn text-[12px]">Stake</Link>
            </div>
          </div>
        </div>

        {/* Level */}
        <div className="bento" data-testid="stat-level">
          <div className="flex items-center justify-between">
            <div className="eyebrow">Level</div>
            <Zap className="text-accent-aurora" size={16} strokeWidth={1.8}/>
          </div>
          <div className="font-display font-bold text-[3rem] tabular tracking-[-0.04em] grad-aurora leading-none mt-3">{stats?.level ?? 1}</div>
          <div className="mt-4">
            <div className="h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
              <div className="h-full rounded-full transition-all" style={{ width: `${xpPct}%`, background: 'linear-gradient(90deg, #6EE7F9, #A78BFA)' }} />
            </div>
            <div className="text-[11px] mt-2 text-white/50 tabular">{stats?.xp ?? 0} / {(stats?.level ?? 1) * 100} XP</div>
          </div>
        </div>
      </div>

      {/* Secondary metrics row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="bento" data-testid="stat-distance">
          <div className="eyebrow">Distance</div>
          <div className="font-display font-bold text-[1.85rem] tabular tracking-[-0.03em] mt-2">
            <CountUp value={stats?.totalDistance ?? 0} decimals={2} /> <span className="text-sm text-white/35 font-normal">km</span>
          </div>
          <TrendingUp className="text-accent-aurora/60 mt-2" size={15}/>
        </div>

        <div className="bento" data-testid="stat-rides">
          <div className="eyebrow">Total Rides</div>
          <div className="font-display font-bold text-[1.85rem] tabular tracking-[-0.03em] mt-2">
            <CountUp value={stats?.totalRides ?? 0} />
          </div>
          <Bike className="text-accent-mint/60 mt-2" size={15}/>
        </div>

        <Link to="/carbon" className="bento group" data-testid="stat-carbon">
          <div className="flex items-center justify-between">
            <div className="eyebrow">CO₂ Saved</div>
            <Leaf className="text-accent-mint" size={15}/>
          </div>
          <div className="font-display font-bold text-[1.85rem] text-accent-mint tabular tracking-[-0.03em] mt-2">
            <CountUp value={carbon?.lifetime?.totals?.saved_kg ?? 0} decimals={2} /> <span className="text-sm text-white/35 font-normal">kg</span>
          </div>
          <div className="text-[11px] text-white/45 mt-1">Rank #{carbon?.monthly_rank ?? '—'} this month →</div>
        </Link>

        <Link to="/airdrops" className="bento group" data-testid="stat-airdrop">
          <div className="flex items-center justify-between">
            <div className="eyebrow">Airdrops</div>
            <MapPin className="text-accent-rose" size={15}/>
          </div>
          <div className="font-display font-bold text-[1.85rem] tracking-[-0.03em] mt-2">Hunt</div>
          <div className="text-[11px] text-white/45 mt-1">Geo-located VOLTZ drops →</div>
        </Link>
      </div>

      {/* Quick actions */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="eyebrow">Quick actions</div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { to: '/challenges',   icon: Target, label: 'Quests',       color: 'text-accent-gold' },
            { to: '/achievements', icon: Award,  label: 'Achievements', color: 'text-accent-violet' },
            { to: '/marketplace',  icon: Gift,   label: 'Marketplace',  color: 'text-accent-aurora' },
            { to: '/leaderboard',  icon: Trophy, label: 'Leaderboard',  color: 'text-accent-rose' },
          ].map((q) => {
            const I = q.icon;
            return (
              <Link key={q.to} to={q.to} className="bento group flex items-center gap-3" data-testid={`qa-${q.label.toLowerCase()}`}>
                <div className={`w-9 h-9 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center ${q.color}`}>
                  <I size={17} strokeWidth={1.8}/>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm">{q.label}</div>
                </div>
                <ArrowRight size={15} className="text-white/30 group-hover:text-white/60 transition-colors"/>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Recent rides */}
      <div className="bento">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="eyebrow">Recent activity</div>
            <div className="font-display font-semibold text-lg tracking-tight mt-0.5">Latest rides</div>
          </div>
          <Link to="/ride" className="text-[12px] text-accent-aurora hover:text-white inline-flex items-center gap-1">Track new <ArrowRight size={12} /></Link>
        </div>
        {loading ? (
          <div className="py-10 flex justify-center"><div className="cyber-spinner"/></div>
        ) : recent.length === 0 ? (
          <div className="py-10 text-center">
            <Sparkles className="mx-auto mb-2 text-white/30" size={20}/>
            <div className="text-white/55 text-sm">No rides yet. <Link to="/ride" className="text-accent-aurora underline-offset-2 hover:underline">Start your first one</Link>.</div>
          </div>
        ) : (
          <div className="divide-y divide-white/[0.04]">
            {recent.map((r) => (
              <div key={r.ride_id} className="py-3 flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center text-accent-mint">
                  <Bike size={17} strokeWidth={1.8}/>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm tabular">{(r.distance ?? 0).toFixed(2)} km <span className="text-white/45 font-normal">· {r.vehicle_type}</span></div>
                  <div className="text-[11px] text-white/40 mt-0.5">{new Date(r.start_time).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</div>
                </div>
                <div className="text-accent-gold font-semibold text-sm tabular">+{(r.rmr_earned ?? 0).toFixed(2)} VOLTZ</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
