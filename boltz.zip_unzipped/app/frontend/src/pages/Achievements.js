import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { toast } from 'sonner';
import {
  Award as AwardIcon, Bike, Flame, Trophy, Map, Globe, Medal, Zap,
  Gift, Target, Crown, ShoppingCart, Wallet as WalletIcon, Star, Diamond, Lock
} from 'lucide-react';

const ICONS = {
  bicycle: Bike, fire: Flame, trophy: Trophy, map: Map, globe: Globe, medal: Medal,
  lightning: Zap, gift: Gift, target: Target, crown: Crown, cart: ShoppingCart, wallet: WalletIcon, star: Star, diamond: Diamond,
};

export default function Achievements() {
  const [items, setItems] = useState([]);
  const [busy, setBusy] = useState(null);

  const load = async () => {
    try { const { data } = await api.get('/achievements'); setItems(data); } catch { /* non-fatal */ }
  };
  useEffect(() => { load(); }, []);

  const claim = async (a) => {
    setBusy(a.id);
    try {
      const r = await api.post(`/achievements/${a.id}/claim`);
      toast.success(`Unlocked: ${a.title} — +${r.data.rmr_earned} VOLTZ`);
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Not unlocked yet'); }
    finally { setBusy(null); }
  };

  return (
    <div className="fade-in space-y-6">
      <div>
        <div className="text-[11px] tracking-[0.3em] text-white/50">// NFT BADGES</div>
        <h1 className="font-display font-bold text-3xl sm:text-4xl mt-1 gradient-text">Achievement NFTs</h1>
        <p className="text-white/55 mt-1">Mint unique on-chain badges as you progress.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map(a => {
          const I = ICONS[a.icon] || AwardIcon;
          const ready = a.progress >= a.requirement && !a.claimed;
          const claimed = a.claimed;
          return (
            <div key={a.id} className={`bento rare-glow-${a.rarity}`} data-testid={`ach-${a.id}`}>
              <div className="flex items-start justify-between">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center neon-border-gold ${claimed ? '' : 'opacity-80'}`}>
                  <I size={26} className="text-neon-gold"/>
                </div>
                <span className="text-[10px] tracking-widest uppercase text-white/60">{a.rarity}</span>
              </div>
              <h3 className="mt-2 font-display font-bold text-lg">{a.title}</h3>
              <p className="text-white/65 text-sm">{a.description}</p>
              <div className="mt-3">
                <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                  <div className="h-full" style={{ width: `${Math.min(100, (a.progress / a.requirement) * 100)}%`, background: 'linear-gradient(90deg, #FFD700, #FF33CC)' }} />
                </div>
                <div className="text-[10px] text-white/55 mt-1">{a.progress} / {a.requirement}</div>
              </div>
              <div className="mt-3 flex items-center gap-2 text-xs">
                <span className="text-neon-gold font-display font-bold">+{a.rmr_reward} VOLTZ</span>
                {a.nft_signature && (
                  <a target="_blank" rel="noopener noreferrer" href={`https://explorer.solana.com/tx/${a.nft_signature}?cluster=devnet`} className="text-neon-blue underline">on-chain</a>
                )}
              </div>
              <div className="mt-3">
                {claimed ? (
                  <div className="text-center text-neon-green text-xs inline-flex items-center justify-center gap-1 w-full"><AwardIcon size={12}/> Claimed</div>
                ) : ready ? (
                  <button onClick={() => claim(a)} disabled={busy === a.id} className="btn-neon btn-neon-gold text-xs w-full justify-center" data-testid={`ach-claim-${a.id}`}>Mint NFT</button>
                ) : (
                  <div className="text-center text-white/50 text-xs inline-flex items-center justify-center gap-1 w-full"><Lock size={12}/> Locked</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
