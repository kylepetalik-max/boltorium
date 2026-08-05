import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';
import CountUp from '@/components/CountUp';
import {
  Wallet as WalletIcon, Send, Coins, Link as LinkIcon, ExternalLink,
  Plus, Minus, ChevronRight, Lock, TrendingUp
} from 'lucide-react';

const PACKAGES_FALLBACK = [
  { id: 'rmr_100', name: '100 VOLTZ', rmr: 100, price_cad: 9.99 },
  { id: 'rmr_500', name: '500 VOLTZ', rmr: 500, price_cad: 39.99 },
  { id: 'rmr_1000', name: '1000 VOLTZ', rmr: 1000, price_cad: 69.99 },
];

export default function Wallet() {
  const { user, refresh } = useAuth();
  const [balance, setBalance] = useState(null);
  const [solanaStatus, setSolanaStatus] = useState(null);
  const [packages, setPackages] = useState([]);
  const [walletInput, setWalletInput] = useState('');
  const [transferTo, setTransferTo] = useState('');
  const [transferAmt, setTransferAmt] = useState('');
  const [mintAmt, setMintAmt] = useState('');
  const [tiers, setTiers] = useState([]);
  const [positions, setPositions] = useState([]);
  const [stakeAmt, setStakeAmt] = useState('');
  const [stakeTier, setStakeTier] = useState('7d');
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      const [b, s, p, t, pos] = await Promise.all([
        api.get('/wallet/balance'),
        api.get('/solana/status'),
        api.get('/payments/packages').catch(() => ({ data: PACKAGES_FALLBACK })),
        api.get('/staking/tiers'),
        api.get('/staking/positions'),
      ]);
      setBalance(b.data); setSolanaStatus(s.data);
      setPackages(p.data); setTiers(t.data); setPositions(pos.data);
      setWalletInput(b.data?.walletAddress || '');
    } catch { /* non-fatal */ }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  // Stripe checkout return - poll status
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sid = params.get('session_id');
    if (!sid) return;
    (async () => {
      try {
        const { data } = await api.get(`/payments/status/${sid}`);
        if (data.payment_status === 'paid' && data.rmr_credited > 0) {
          toast.success(`Credited ${data.rmr_credited} VOLTZ!`);
          await refresh(); load();
        } else if (data.status !== 'completed') {
          toast.info('Payment pending…');
        }
      } catch { /* non-fatal */ }
      window.history.replaceState({}, '', '/wallet');
    })();
  }, [refresh]);

  const linkWallet = async () => {
    if (!walletInput || walletInput.length < 32) return toast.error('Enter a valid Solana wallet (32+ chars)');
    setBusy(true);
    try {
      await api.post('/wallet/link', { walletAddress: walletInput });
      toast.success('Wallet linked');
      await refresh(); load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
    finally { setBusy(false); }
  };

  const mint = async () => {
    const amt = parseFloat(mintAmt);
    if (!amt || amt <= 0) return toast.error('Enter amount');
    setBusy(true);
    try {
      const { data } = await api.post('/solana/mint', { amount: amt });
      toast.success(`Minted ${amt} VOLTZ to wallet (${data.minting_mode})`);
      setMintAmt('');
      await refresh(); load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
    finally { setBusy(false); }
  };

  const transfer = async () => {
    if (!transferTo || transferTo.length < 32) return toast.error('Enter valid recipient wallet');
    const amt = parseFloat(transferAmt);
    if (!amt || amt <= 0) return toast.error('Enter amount');
    setBusy(true);
    try {
      const { data } = await api.post('/solana/transfer', { to_wallet: transferTo, amount: amt });
      toast.success(`Sent ${amt} VOLTZ (${data.mode})`);
      setTransferTo(''); setTransferAmt('');
      await refresh(); load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
    finally { setBusy(false); }
  };

  const buy = async (pkg) => {
    setBusy(true);
    try {
      const { data } = await api.post('/payments/checkout', { package_id: pkg.id, origin_url: window.location.origin });
      window.location.href = data.url;
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); setBusy(false); }
  };

  const stake = async () => {
    const amt = parseFloat(stakeAmt);
    if (!amt || amt <= 0) return toast.error('Enter amount');
    setBusy(true);
    try {
      await api.post('/staking/stake', { amount: amt, tier: stakeTier });
      toast.success(`Staked ${amt} VOLTZ — ${stakeTier}`);
      setStakeAmt('');
      await refresh(); load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
    finally { setBusy(false); }
  };

  const unstake = async (id) => {
    setBusy(true);
    try {
      const { data } = await api.post(`/staking/${id}/unstake`);
      toast.success(`Unstaked: principal ${data.principal}, reward ${data.reward}, penalty ${data.penalty}`);
      await refresh(); load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
    finally { setBusy(false); }
  };

  return (
    <div className="fade-in space-y-6">
      <div>
        <div className="text-[11px] tracking-[0.3em] text-white/50">// WALLET</div>
        <h1 className="font-display font-bold text-3xl sm:text-4xl mt-1 gradient-text">VOLTZ Wallet</h1>
      </div>

      {/* Balances */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bento neon-border-gold md:col-span-2" data-testid="wallet-balance">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-[10px] tracking-[0.3em] text-white/50 uppercase">In-App VOLTZ</div>
              <div className="font-display font-black text-5xl text-neon-gold mt-2">
                <CountUp value={balance?.inAppBalance ?? user?.rmr_balance ?? 0} decimals={2} />
              </div>
              <div className="text-[11px] text-white/55 mt-1">On-chain tracked: {balance?.onChainBalance?.toFixed(2) ?? 0} VOLTZ</div>
            </div>
            <WalletIcon className="text-neon-gold opacity-50" size={56}/>
          </div>
        </div>
        <div className="bento" data-testid="solana-status">
          <div className="text-[10px] tracking-[0.3em] text-white/50 uppercase">Solana Network</div>
          <div className="flex items-center gap-2 mt-2">
            <span className={`pulse-dot ${solanaStatus?.connected ? '' : 'opacity-30'}`}/>
            <span className="font-display tracking-wider">{solanaStatus?.connected ? 'CONNECTED' : 'OFFLINE'}</span>
          </div>
          <div className="text-xs text-white/60 mt-2 space-y-1">
            <div>Cluster: <span className="text-neon-blue">{solanaStatus?.cluster}</span></div>
            <div>Mode: <span className={solanaStatus?.mode === 'live' ? 'text-neon-green' : 'text-neon-pink'}>{solanaStatus?.mode}</span></div>
            <div>Core: {solanaStatus?.version || '—'}</div>
          </div>
        </div>
      </div>

      {/* Link wallet */}
      <div className="bento">
        <div className="text-xs tracking-widest text-white/50 uppercase mb-3">Linked Solana Wallet</div>
        <div className="flex gap-2">
          <input className="input-cy flex-1 font-mono text-sm" placeholder="Your Solana wallet address" value={walletInput} onChange={(e) => setWalletInput(e.target.value)} data-testid="wallet-input"/>
          <button onClick={linkWallet} disabled={busy} className="btn-neon" data-testid="wallet-link"><LinkIcon size={14} className="mr-1"/> Link</button>
        </div>
        {balance?.walletAddress && (
          <a target="_blank" rel="noopener noreferrer" href={`https://explorer.solana.com/address/${balance.walletAddress}?cluster=devnet`} className="text-[11px] inline-flex items-center text-neon-blue mt-2">
            View on Solana Explorer <ExternalLink size={11} className="ml-1"/>
          </a>
        )}
      </div>

      {/* Mint / Transfer */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bento">
          <div className="text-xs tracking-widest text-white/50 uppercase mb-3">Mint to On-Chain Wallet</div>
          <div className="flex gap-2">
            <input type="number" min="0" className="input-cy flex-1" placeholder="Amount VOLTZ" value={mintAmt} onChange={(e) => setMintAmt(e.target.value)} data-testid="mint-amount"/>
            <button onClick={mint} disabled={busy || !user?.wallet_address} className="btn-neon btn-neon-gold" data-testid="mint-btn"><Coins size={14} className="mr-1"/> Mint</button>
          </div>
          <div className="text-[11px] text-white/55 mt-2">Deducts from in-app balance, mints SPL to your linked wallet.</div>
        </div>
        <div className="bento">
          <div className="text-xs tracking-widest text-white/50 uppercase mb-3">P2P Transfer</div>
          <input className="input-cy mb-2 font-mono text-sm" placeholder="Recipient wallet" value={transferTo} onChange={(e) => setTransferTo(e.target.value)} data-testid="transfer-to"/>
          <div className="flex gap-2">
            <input type="number" min="0" className="input-cy flex-1" placeholder="Amount" value={transferAmt} onChange={(e) => setTransferAmt(e.target.value)} data-testid="transfer-amount"/>
            <button onClick={transfer} disabled={busy} className="btn-neon btn-neon-pink" data-testid="transfer-btn"><Send size={14} className="mr-1"/> Send</button>
          </div>
        </div>
      </div>

      {/* Buy VOLTZ */}
      <div className="bento">
        <div className="text-xs tracking-widest text-white/50 uppercase mb-3">Buy VOLTZ — Stripe (Test mode)</div>
        <div className="grid sm:grid-cols-3 gap-3">
          {packages.map(p => (
            <div key={p.id} className="bento neon-border-blue text-center">
              <div className="font-display text-2xl font-bold text-neon-gold">{p.rmr} VOLTZ</div>
              <div className="text-white/70 text-sm">CAD ${p.price_cad?.toFixed(2)}</div>
              <button onClick={() => buy(p)} disabled={busy} className="btn-neon btn-neon-gold mt-3 w-full text-xs" data-testid={`buy-${p.id}`}><Plus size={12} className="mr-1"/> Buy</button>
            </div>
          ))}
        </div>
      </div>

      {/* Staking */}
      <div className="bento">
        <div className="flex items-center justify-between mb-3">
          <div className="text-xs tracking-widest text-white/50 uppercase">Staking</div>
          <TrendingUp className="text-neon-green" size={16}/>
        </div>
        <div className="grid sm:grid-cols-3 gap-3 mb-4">
          {tiers.map(t => (
            <button key={t.id} onClick={() => setStakeTier(t.id)} className={`bento text-left ${stakeTier === t.id ? 'neon-border-green' : ''}`} data-testid={`tier-${t.id}`}>
              <div className="font-display font-bold text-lg">{t.label}</div>
              <div className="text-neon-green text-2xl font-display font-bold">{t.apy}% <span className="text-xs text-white/50">APY</span></div>
              <div className="text-[10px] text-white/50">Min {t.min_amount} VOLTZ</div>
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input type="number" className="input-cy flex-1" placeholder="Amount to stake" value={stakeAmt} onChange={(e) => setStakeAmt(e.target.value)} data-testid="stake-amount"/>
          <button onClick={stake} disabled={busy} className="btn-neon btn-neon-green" data-testid="stake-btn"><Lock size={14} className="mr-1"/> Stake</button>
        </div>

        {positions.length > 0 && (
          <div className="mt-4 space-y-2">
            {positions.map(p => (
              <div key={p.stake_id} className="bento flex items-center justify-between text-sm">
                <div>
                  <div className="font-display font-bold">{p.amount} VOLTZ • {p.tier}</div>
                  <div className="text-[11px] text-white/55">Unlocks {new Date(p.unlock_at).toLocaleDateString()} • APY {p.apy}%</div>
                  <div className="text-[11px] text-neon-green">Earned so far {p.earned_so_far?.toFixed(2)} VOLTZ</div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-1 rounded ${p.is_unlocked ? 'text-neon-green' : 'text-white/50'}`}>{p.is_unlocked ? 'UNLOCKED' : 'LOCKED'}</span>
                  {p.status === 'active' && (
                    <button onClick={() => unstake(p.stake_id)} disabled={busy} className="btn-neon btn-ghost text-xs" data-testid={`unstake-${p.stake_id}`}>
                      <Minus size={12} className="mr-1"/> Unstake
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
