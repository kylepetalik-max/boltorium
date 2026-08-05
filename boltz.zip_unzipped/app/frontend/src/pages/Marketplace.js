import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';
import { ShoppingBag, Tag, Coins, Search } from 'lucide-react';

const CATEGORIES = ['all', 'vehicles', 'parts', 'gear', 'merch', 'bike'];

export default function Marketplace() {
  const { refresh } = useAuth();
  const [items, setItems] = useState([]);
  const [cat, setCat] = useState('all');
  const [q, setQ] = useState('');
  const [busy, setBusy] = useState(null);

  useEffect(() => {
    (async () => {
      const url = cat === 'all' ? '/marketplace/items' : `/marketplace/items?category=${cat}`;
      try { const { data } = await api.get(url); setItems(data); } catch { /* non-fatal */ }
    })();
  }, [cat]);

  const filtered = items.filter(i => !q || (i.name || '').toLowerCase().includes(q.toLowerCase()) || (i.brand || '').toLowerCase().includes(q.toLowerCase()));

  const buy = async (item, method) => {
    setBusy(item.item_id);
    try {
      const { data } = await api.post('/marketplace/purchase', { item_id: item.item_id, payment_method: method });
      if (method === 'rmr') {
        toast.success(`Purchased ${item.name} for ${data.price_paid} VOLTZ`);
        await refresh();
      } else {
        toast.success(`SOL payment pending: ${data.sol_amount} SOL`);
      }
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
    finally { setBusy(null); }
  };

  return (
    <div className="fade-in space-y-4">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-2">
        <div>
          <div className="text-[11px] tracking-[0.3em] text-white/50">// MARKETPLACE</div>
          <h1 className="font-display font-bold text-3xl sm:text-4xl mt-1 gradient-text">Shop & Trade</h1>
          <p className="text-white/55 text-sm mt-1">Spend VOLTZ or SOL on real gear. 1 SOL = 1000 VOLTZ.</p>
        </div>
        <div className="flex items-center gap-2 bg-white/5 rounded-xl px-3 py-2 w-full md:w-80">
          <Search size={14} className="text-white/60"/>
          <input className="bg-transparent flex-1 outline-none text-sm" placeholder="Search products…" value={q} onChange={e => setQ(e.target.value)} data-testid="shop-search"/>
        </div>
      </div>

      <div className="flex gap-2 overflow-x-auto no-scrollbar">
        {CATEGORIES.map(c => (
          <button key={c} onClick={() => setCat(c)}
            className={`px-3 py-1.5 rounded-lg text-xs font-display tracking-wider uppercase whitespace-nowrap ${cat === c ? 'bg-white/15 text-neon-cyan' : 'bg-white/5 text-white/60'}`}
            data-testid={`cat-${c}`}>{c}</button>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filtered.map(item => {
          const solPrice = (item.price_rmr / 1000).toFixed(3);
          return (
            <div key={item.item_id} className="bento overflow-hidden" data-testid={`item-${item.item_id}`}>
              <div className="h-44 -mx-5 -mt-5 mb-3 bg-white/5 overflow-hidden flex items-center justify-center relative">
                {item.image_url ? <img src={item.image_url} alt={item.name} className="w-full h-full object-cover"/> : <ShoppingBag className="text-white/30" size={48}/>}
                {item.is_featured && <span className="absolute top-2 left-2 px-2 py-0.5 rounded-full text-[10px] bg-yellow-400/20 text-neon-gold border border-yellow-400/30">FEATURED</span>}
              </div>
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="text-[10px] tracking-widest text-white/45 uppercase">{item.brand}</div>
                  <div className="font-display font-bold text-sm truncate">{item.name}</div>
                </div>
                <Tag size={14} className="text-white/40 mt-1"/>
              </div>
              <div className="mt-2 flex items-end justify-between">
                <div>
                  <div className="text-neon-gold font-display font-bold text-xl">{item.price_rmr?.toFixed(0)} VOLTZ</div>
                  <div className="text-[10px] text-white/50">~ {solPrice} SOL</div>
                </div>
                <div className="text-[10px] text-white/45">Stock: {item.stock ?? '—'}</div>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2">
                <button onClick={() => buy(item, 'rmr')} disabled={busy === item.item_id} className="btn-neon btn-neon-gold text-[11px] justify-center" data-testid={`buy-rmr-${item.item_id}`}>VOLTZ</button>
                <button onClick={() => buy(item, 'sol')} disabled={busy === item.item_id} className="btn-neon btn-neon-pink text-[11px] justify-center" data-testid={`buy-sol-${item.item_id}`}>SOL</button>
              </div>
            </div>
          );
        })}
        {filtered.length === 0 && <div className="bento col-span-full text-center py-10 text-white/55"><Coins className="mx-auto mb-2"/> No items match</div>}
      </div>
    </div>
  );
}
