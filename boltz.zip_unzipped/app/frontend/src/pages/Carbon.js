import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import CountUp from '@/components/CountUp';
import {
  Leaf, TreePine, Car, Smartphone, Globe, Award, Trophy,
  TrendingDown, Crown, Users, Sparkles, Calendar, ExternalLink, ArrowUpRight
} from 'lucide-react';

const VEHICLE_LABELS = {
  bicycle: 'Bicycle', skateboard: 'Skateboard', ebike: 'E-Bike',
  electric_skateboard: 'E-Skateboard', onewheel: 'Onewheel', euc: 'EUC',
  dirt_bike: 'Dirt Bike (gas)', electric_dirt_bike: 'Electric Dirt Bike',
};

export default function Carbon() {
  const { user } = useAuth();
  const [me, setMe] = useState(null);
  const [board, setBoard] = useState(null);
  const [globalStats, setGlobalStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [m, lb, gs, h] = await Promise.all([
          api.get('/carbon/me'),
          api.get('/carbon/leaderboard'),
          api.get('/carbon/stats'),
          api.get('/carbon/awards'),
        ]);
        setMe(m.data); setBoard(lb.data); setGlobalStats(gs.data); setHistory(h.data);
      } finally { setLoading(false); }
    })();
  }, []);

  if (loading) return <div className="py-20 flex justify-center"><div className="cyber-spinner"/></div>;

  const monthlyRank = me?.monthly_rank;
  const totalRiders = me?.monthly_total_riders ?? 0;
  const monthLabel = me?.month?.label;
  const lifetime = me?.lifetime?.totals;
  const monthly = me?.monthly?.totals;

  return (
    <div className="fade-in space-y-7">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <div className="eyebrow">Carbon Footprint · {monthLabel || 'This month'}</div>
          <h1 className="font-display font-bold text-[2.25rem] sm:text-[2.75rem] mt-1.5 tracking-[-0.03em] leading-[1.05]">
            <span className="grad-headline">You&apos;ve saved</span>{' '}
            <span className="grad-mint tabular"><CountUp value={lifetime?.saved_kg ?? 0} decimals={2}/></span>{' '}
            <span className="grad-headline">kg CO₂</span>
          </h1>
          <p className="text-white/55 text-[14px] mt-2 max-w-2xl">
            Versus driving a typical gasoline car. Riding your <span className="text-accent-aurora">{user?.vehicle_type || 'ebike'}</span> instead protects the planet — and the top eco-rider each month wins a Solana VOLTZ airdrop.
          </p>
        </div>
        <Link to="/ride" className="btn btn-mint" data-testid="carbon-cta-ride"><Calendar size={14}/> Track a ride <ArrowUpRight size={13}/></Link>
      </div>

      {/* Impact stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <ImpactCard icon={TreePine}   label="Tree-years"      value={lifetime?.trees_equivalent ?? 0}    decimals={2} color="text-accent-mint"/>
        <ImpactCard icon={Car}        label="Car km offset"   value={lifetime?.car_km_offset ?? 0}       decimals={1} color="text-accent-aurora"/>
        <ImpactCard icon={Smartphone} label="Phone charges"   value={lifetime?.smartphone_charges ?? 0}  decimals={0} color="text-accent-violet"/>
        <ImpactCard icon={TrendingDown} label="Clean km"       value={lifetime?.distance_km ?? 0}         decimals={2} color="text-accent-gold"/>
      </div>

      {/* Rank + Monthly */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bento ring-gold relative overflow-hidden" data-testid="carbon-monthly-rank">
          <div className="absolute -top-24 -right-20 w-72 h-72 rounded-full" style={{ background: 'radial-gradient(circle, rgba(245,200,66,0.18), transparent 65%)' }}/>
          <div className="relative">
            <div className="flex items-center justify-between">
              <div className="eyebrow">Monthly rank</div>
              <Trophy className="text-accent-gold" size={17}/>
            </div>
            <div className="font-display font-bold text-[4.5rem] grad-gold tabular tracking-[-0.04em] mt-2 leading-none">#{monthlyRank ?? '—'}</div>
            <div className="text-[13px] text-white/55 mt-2">of {totalRiders} eco-rider{totalRiders === 1 ? '' : 's'} this month</div>
            <div className="mt-4 p-3 rounded-lg bg-accent-gold/5 border border-accent-gold/15">
              <div className="text-[11px] text-white/55">Top rider wins</div>
              <div className="text-accent-gold font-semibold text-sm">500 VOLTZ airdrop · on-chain at month end</div>
            </div>
          </div>
        </div>

        <div className="bento lg:col-span-2" data-testid="carbon-month-stats">
          <div className="eyebrow">This month — {monthLabel}</div>
          <div className="grid sm:grid-cols-3 gap-4 mt-3">
            <MiniStat label="CO₂ saved" value={monthly?.saved_kg ?? 0} suffix=" kg" color="text-accent-mint"  decimals={2}/>
            <MiniStat label="Distance"  value={monthly?.distance_km ?? 0} suffix=" km" color="text-accent-aurora" decimals={2}/>
            <MiniStat label="Rides"     value={monthly?.rides ?? 0}                  color="text-accent-rose"/>
          </div>
          {(me?.lifetime?.by_vehicle?.length ?? 0) > 0 && (
            <div className="mt-6">
              <div className="eyebrow mb-3">By vehicle — lifetime</div>
              <div className="space-y-3">
                {me.lifetime.by_vehicle.map(v => {
                  const max = Math.max(...me.lifetime.by_vehicle.map(x => x.saved_kg)) || 1;
                  return (
                    <div key={v.vehicle}>
                      <div className="flex justify-between text-[12px] mb-1.5">
                        <span className="text-white/80">{VEHICLE_LABELS[v.vehicle] || v.vehicle}</span>
                        <span className="text-accent-mint tabular">{v.saved_kg.toFixed(2)} kg</span>
                      </div>
                      <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                        <div className="h-full rounded-full" style={{ width: `${(v.saved_kg/max)*100}%`, background: 'linear-gradient(90deg, #34E0A1, #6EE7F9)' }}/>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Monthly Leaderboard */}
      <div className="bento" data-testid="carbon-leaderboard">
        <div className="flex items-center justify-between mb-5">
          <div>
            <div className="eyebrow">Monthly eco-riders</div>
            <div className="font-display font-semibold text-xl tracking-tight mt-0.5">Top CO₂ savers — {monthLabel}</div>
          </div>
          <Users className="text-accent-mint" size={18}/>
        </div>
        {(board?.leaderboard?.length ?? 0) === 0 ? (
          <div className="py-10 text-center">
            <Sparkles className="mx-auto mb-2 text-white/30" size={20}/>
            <div className="text-white/55 text-sm">No rides this month yet. <Link to="/ride" className="text-accent-aurora underline-offset-2 hover:underline">Take the first eco-ride</Link>.</div>
          </div>
        ) : (
          <div className="space-y-1">
            {board.leaderboard.slice(0, 10).map((r, i) => {
              const isMe = r.user_id === user?.user_id;
              return (
                <div key={r.user_id} className={`flex items-center gap-4 px-3 py-3 rounded-xl ${i === 0 ? 'bg-accent-gold/[0.06] border border-accent-gold/15' : 'border border-transparent'} ${isMe ? 'ring-1 ring-accent-aurora/30' : ''} hover:bg-white/[0.03] transition-colors`}>
                  <div className="w-10 text-center">
                    {i === 0 ? <Crown className="text-accent-gold mx-auto" size={20}/> : <span className={`font-display font-semibold text-base tabular ${i < 3 ? 'text-accent-rose' : 'text-white/55'}`}>#{i+1}</span>}
                  </div>
                  <div className="w-10 h-10 rounded-lg overflow-hidden bg-white/[0.04] border border-white/[0.06] flex items-center justify-center">
                    {r.picture ? <img src={r.picture} alt="" className="w-full h-full object-cover"/> : <Leaf className="text-accent-mint" size={16}/>}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate">{(r.name || r.first_name || 'Rider')}{isMe && <span className="ml-2 text-[10px] text-accent-aurora">you</span>}</div>
                    <div className="text-[11px] text-white/45 mt-0.5">{r.rides} ride{r.rides === 1 ? '' : 's'} · {r.distance_km.toFixed(1)} km · {VEHICLE_LABELS[r.primary_vehicle] || r.primary_vehicle}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-display font-semibold text-accent-mint text-base tabular">{r.saved_kg.toFixed(2)} kg</div>
                    <div className="text-[10px] text-white/45 tabular">{r.trees_equivalent} trees</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Hall of Fame */}
      {history.length > 0 && (
        <div className="bento" data-testid="carbon-last-winner">
          <div className="flex items-center gap-2 mb-3">
            <Award size={17} className="text-accent-gold"/>
            <div className="eyebrow">Hall of fame</div>
          </div>
          <div className="space-y-2">
            {history.slice(0, 5).map((w) => (
              <div key={w.award_id} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 p-3 rounded-xl bg-white/[0.025] border border-white/[0.04]">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg ring-gold flex items-center justify-center bg-accent-gold/5"><Crown className="text-accent-gold" size={17}/></div>
                  <div>
                    <div className="font-semibold text-sm">{w.winner_name || 'Anonymous Rider'}</div>
                    <div className="text-[11px] text-white/50">{w.month_label} · {w.saved_kg?.toFixed(2)} kg CO₂ · {w.rides} rides</div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-accent-gold font-semibold text-sm tabular">+{w.reward_rmr} VOLTZ</div>
                  {w.explorer_url && <a target="_blank" rel="noopener noreferrer" href={w.explorer_url} className="text-accent-aurora text-[11px] inline-flex items-center gap-1">on-chain <ExternalLink size={11}/></a>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Global */}
      <div className="bento">
        <div className="flex items-center justify-between mb-4">
          <div className="eyebrow">VOLTZ community impact</div>
          <Globe className="text-accent-aurora" size={17}/>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <MiniStat label="Total CO₂ saved" value={globalStats?.total_saved_kg ?? 0} suffix=" kg" color="text-accent-mint"  decimals={2}/>
          <MiniStat label="Trees equivalent" value={globalStats?.trees_equivalent ?? 0} color="text-accent-gold"   decimals={2}/>
          <MiniStat label="Distance ridden" value={globalStats?.total_distance_km ?? 0} suffix=" km" color="text-accent-aurora" decimals={2}/>
          <MiniStat label="Eco rides"       value={globalStats?.total_rides ?? 0} color="text-accent-rose"/>
        </div>
      </div>
    </div>
  );
}

function ImpactCard({ icon: I, label, value, color, decimals = 0 }) {
  return (
    <div className="bento">
      <div className="flex items-center justify-between">
        <I className={color} size={16} strokeWidth={1.8}/>
      </div>
      <div className="font-display font-bold text-[1.85rem] tabular tracking-[-0.03em] mt-3"><CountUp value={value} decimals={decimals}/></div>
      <div className="eyebrow mt-1">{label}</div>
    </div>
  );
}

function MiniStat({ label, value, suffix = '', color = 'text-white', decimals = 0 }) {
  return (
    <div>
      <div className="eyebrow mb-1">{label}</div>
      <div className={`font-display font-bold text-[1.5rem] tabular tracking-[-0.03em] ${color}`}><CountUp value={value} decimals={decimals}/>{suffix}</div>
    </div>
  );
}
