import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { Trophy, Medal, Award as AwardIcon } from 'lucide-react';

export default function Leaderboard() {
  const [riders, setRiders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try { const { data } = await api.get('/rider/leaderboard'); setRiders(data); }
      finally { setLoading(false); }
    })();
  }, []);

  const top3 = riders.slice(0, 3);
  const rest = riders.slice(3);

  if (loading) return <div className="py-20 flex justify-center"><div className="cyber-spinner"/></div>;

  const colorFor = (i) => i === 0 ? 'text-neon-gold' : i === 1 ? 'text-neon-pink' : i === 2 ? 'text-neon-blue' : 'text-white';

  return (
    <div className="fade-in space-y-6">
      <div>
        <div className="text-[11px] tracking-[0.3em] text-white/50">// LEADERBOARD</div>
        <h1 className="font-display font-bold text-3xl sm:text-4xl mt-1 gradient-text">Top Riders</h1>
      </div>

      {/* Podium */}
      <div className="grid grid-cols-3 gap-4 items-end">
        {[1, 0, 2].map((idx) => {
          const r = top3[idx];
          if (!r) return <div key={idx} />;
          const heights = { 0: 'h-44', 1: 'h-32', 2: 'h-28' };
          const Icons = { 0: Trophy, 1: Medal, 2: AwardIcon };
          const Border = { 0: 'neon-border-gold', 1: 'neon-border-pink', 2: 'neon-border-blue' };
          const C = { 0: 'text-neon-gold', 1: 'text-neon-pink', 2: 'text-neon-blue' };
          const I = Icons[idx];
          return (
            <div key={idx} className="flex flex-col items-center text-center">
              <div className="w-16 h-16 rounded-full overflow-hidden mb-2 ring-2 ring-white/10">
                {r.picture ? <img src={r.picture} alt="r" className="w-full h-full object-cover"/> : <div className="w-full h-full flex items-center justify-center font-display font-bold">{(r.first_name || r.username || 'R').slice(0,2).toUpperCase()}</div>}
              </div>
              <div className="font-display font-bold truncate max-w-full">{r.first_name} {r.last_name}</div>
              <I className={`${C[idx]} my-2`} size={26}/>
              <div className={`${heights[idx]} w-full bento ${Border[idx]} flex flex-col items-center justify-center`}>
                <div className={`font-display font-black text-3xl ${C[idx]}`}>{r.rmr_balance?.toFixed(0) ?? 0}</div>
                <div className="text-[10px] tracking-widest text-white/50 uppercase">VOLTZ</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Rest */}
      <div className="bento">
        <div className="text-xs tracking-widest text-white/50 uppercase mb-3">Full Rankings</div>
        <div className="divide-y divide-white/5">
          {rest.map((r, i) => (
            <div key={r.user_id} className="py-3 flex items-center gap-3">
              <div className={`w-8 text-center font-display font-bold ${colorFor(i + 3)}`}>#{i + 4}</div>
              <div className="w-10 h-10 rounded-lg overflow-hidden bg-white/5 flex items-center justify-center">
                {r.picture ? <img src={r.picture} alt="" className="w-full h-full object-cover"/> : <span className="font-display font-bold text-sm">{(r.first_name || 'R').slice(0,1).toUpperCase()}</span>}
              </div>
              <div className="flex-1">
                <div className="font-body">{r.first_name} {r.last_name}</div>
                <div className="text-[11px] text-white/50">{(r.total_distance ?? 0).toFixed(2)} km • {r.total_rides ?? 0} rides</div>
              </div>
              <div className="text-neon-gold font-display font-bold">{(r.rmr_balance ?? 0).toFixed(0)} <span className="text-[10px] text-white/40">VOLTZ</span></div>
            </div>
          ))}
          {rest.length === 0 && top3.length === 0 && (
            <div className="py-10 text-center text-white/50">No riders yet — be the first!</div>
          )}
        </div>
      </div>
    </div>
  );
}
