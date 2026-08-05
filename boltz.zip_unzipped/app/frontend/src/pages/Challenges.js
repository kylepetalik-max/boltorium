import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { toast } from 'sonner';
import { Target, Zap, Trophy, Award as AwardIcon, Bike, Flag, Gift } from 'lucide-react';

const icons = { bicycle: Bike, road: Flag, flag: Flag, gift: Gift, zap: Zap, target: Target, crown: Trophy };
const diffColor = { rookie: 'text-neon-blue', rider: 'text-neon-pink', pro: 'text-neon-gold' };

export default function Challenges() {
  const [all, setAll] = useState([]);
  const [mine, setMine] = useState([]);
  const [tab, setTab] = useState('all');
  const [busy, setBusy] = useState(null);

  const load = async () => {
    try {
      const [a, m] = await Promise.all([api.get('/challenges'), api.get('/challenges/mine')]);
      setAll(a.data); setMine(m.data);
    } catch { /* non-fatal */ }
  };
  useEffect(() => { load(); }, []);

  const join = async (c) => {
    setBusy(c.challenge_id);
    try {
      await api.post(`/challenges/${c.challenge_id}/join`);
      toast.success(`Joined: ${c.title}`);
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
    finally { setBusy(null); }
  };
  const claim = async (c) => {
    setBusy(c.challenge_id);
    try {
      await api.post(`/challenges/${c.challenge_id}/claim`);
      toast.success('Reward claimed');
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Not completed yet'); }
    finally { setBusy(null); }
  };

  const list = tab === 'all' ? all : mine.map(m => ({ ...m.challenge, _userChallenge: m }));

  return (
    <div className="fade-in space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[11px] tracking-[0.3em] text-white/50">// CHALLENGES</div>
          <h1 className="font-display font-bold text-3xl sm:text-4xl mt-1 gradient-text">Quests & Missions</h1>
        </div>
        <div className="flex bg-white/5 rounded-xl p-1">
          <button onClick={() => setTab('all')} className={`px-3 py-1.5 rounded-lg text-xs font-display tracking-wider uppercase ${tab === 'all' ? 'bg-white/10 text-neon-blue' : 'text-white/60'}`} data-testid="tab-all">All</button>
          <button onClick={() => setTab('mine')} className={`px-3 py-1.5 rounded-lg text-xs font-display tracking-wider uppercase ${tab === 'mine' ? 'bg-white/10 text-neon-pink' : 'text-white/60'}`} data-testid="tab-mine">My Quests</button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {list.map(c => {
          const I = icons[c.icon] || Target;
          const uc = c._userChallenge;
          const pct = uc ? Math.min(100, (uc.progress / c.requirement) * 100) : 0;
          return (
            <div key={c.challenge_id} className="bento" data-testid={`challenge-${c.challenge_id}`}>
              <div className="flex items-start justify-between">
                <I className="text-neon-gold" size={24}/>
                <span className={`text-[10px] tracking-widest uppercase ${diffColor[c.difficulty] || 'text-white/60'}`}>{c.difficulty}</span>
              </div>
              <h3 className="mt-2 font-display font-bold text-lg">{c.title}</h3>
              <p className="text-white/65 text-sm font-body mt-1">{c.description}</p>
              <div className="mt-3 flex items-center gap-3 text-xs">
                <span className="text-neon-gold font-display font-bold">+{c.reward_rmr} VOLTZ</span>
                <span className="text-neon-blue">+{c.reward_xp} XP</span>
              </div>
              {uc && (
                <div className="mt-3">
                  <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                    <div className="h-full" style={{ width: `${pct}%`, background: 'linear-gradient(90deg, #FFD700, #FF33CC)' }} />
                  </div>
                  <div className="text-[10px] mt-1 text-white/50">{uc.progress?.toFixed(1) || 0} / {c.requirement} {c.requirement_unit}</div>
                </div>
              )}
              <div className="mt-3">
                {!uc ? (
                  <button onClick={() => join(c)} disabled={busy === c.challenge_id} className="btn-neon btn-ghost text-xs w-full justify-center" data-testid={`join-${c.challenge_id}`}>
                    Join Quest
                  </button>
                ) : uc.status === 'completed' ? (
                  <button onClick={() => claim(c)} disabled={busy === c.challenge_id} className="btn-neon btn-neon-gold text-xs w-full justify-center" data-testid={`claim-${c.challenge_id}`}>
                    Claim Reward
                  </button>
                ) : uc.status === 'claimed' ? (
                  <div className="text-[11px] text-neon-green text-center inline-flex items-center justify-center gap-1 w-full"><AwardIcon size={12}/> Claimed</div>
                ) : (
                  <div className="text-[11px] text-white/60 text-center w-full">In Progress</div>
                )}
              </div>
            </div>
          );
        })}
        {list.length === 0 && <div className="bento col-span-full text-center text-white/55 py-10">No challenges to show</div>}
      </div>
    </div>
  );
}
