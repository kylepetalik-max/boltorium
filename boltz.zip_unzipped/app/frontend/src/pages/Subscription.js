import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';
import {
  Check, Crown, Star, ChevronRight, Shield, Coins, Calendar,
  Sparkles, Zap, TrendingUp, ArrowUpRight, X
} from 'lucide-react';

const TIER_ICONS = { free: Shield, pro: Star, vip: Crown };
const TIER_COLORS = { free: 'text-white/70', pro: 'text-accent-aurora', vip: 'text-accent-gold' };
const TIER_RING = { free: '', pro: 'ring-aurora', vip: 'ring-gold' };

export default function Subscription() {
  const { user, refresh } = useAuth();
  const navigate = useNavigate();
  const [tiers, setTiers] = useState([]);
  const [me, setMe] = useState(null);
  const [busy, setBusy] = useState(null);
  const [confirm, setConfirm] = useState(null); // {tier, method}

  const load = async () => {
    const [t, m] = await Promise.all([api.get('/subscriptions/tiers'), api.get('/subscriptions/me')]);
    setTiers(t.data); setMe(m.data);
  };
  useEffect(() => { load(); }, []);

  // Handle Stripe return
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sid = params.get('session_id');
    if (sid) {
      (async () => {
        try {
          const { data } = await api.get(`/payments/status/${sid}`);
          if (data.subscription_tier) {
            toast.success(`Welcome to ${data.subscription_tier.toUpperCase()} 🎉`);
            await refresh(); load();
          }
        } catch { /* non-fatal */ }
        window.history.replaceState({}, '', '/subscription');
      })();
    }
    if (params.get('cancelled')) {
      toast.info('Checkout cancelled');
      window.history.replaceState({}, '', '/subscription');
    }
  }, [refresh]);

  const subscribe = async (tier, method) => {
    setBusy(`${tier}_${method}`); setConfirm(null);
    try {
      const { data } = await api.post('/subscriptions/subscribe', {
        tier, payment_method: method,
        origin_url: method === 'stripe' ? window.location.origin : undefined,
      });
      if (method === 'stripe' && data.checkout_url) {
        window.location.href = data.checkout_url;
        return;
      }
      toast.success(`Welcome to ${tier.toUpperCase()}`);
      await refresh(); await load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
    finally { setBusy(null); }
  };

  const cancel = async () => {
    if (!window.confirm('Cancel auto-renewal? You keep access until expiry.')) return;
    try {
      await api.post('/subscriptions/cancel');
      toast.success('Subscription will not renew');
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
  };

  const currentTier = me?.tier || 'free';
  const exp = me?.subscription?.expires_at;
  const isStakeVip = currentTier === 'vip' && !me?.subscription;

  return (
    <div className="fade-in space-y-7 relative">
      {/* Header */}
      <div>
        <div className="eyebrow">Membership</div>
        <h1 className="font-display font-bold text-[2.25rem] sm:text-[2.75rem] mt-1.5 tracking-[-0.03em] leading-[1.05]">
          <span className="grad-headline">Choose your tier.</span>{' '}
          <span className="grad-gold">Unlock the protocol.</span>
        </h1>
        <p className="text-white/55 mt-3 text-[15px] max-w-2xl">
          Boost your earning rate, unlock higher staking APY, and earn the right to vote on the protocol's direction. Pay in fiat, VOLTZ, or stake to unlock.
        </p>
      </div>

      {/* Current status */}
      {me && (
        <div className="bento ring-violet relative overflow-hidden">
          <div className="absolute -top-20 -right-16 w-72 h-72 rounded-full" style={{ background: 'radial-gradient(circle, rgba(167,139,250,0.15), transparent 65%)' }}/>
          <div className="relative flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center bg-white/[0.04] border border-white/[0.08]">
                {(() => { const I = TIER_ICONS[currentTier]; return <I size={26} className={TIER_COLORS[currentTier]}/>; })()}
              </div>
              <div>
                <div className="eyebrow">Your tier</div>
                <div className="font-display font-bold text-2xl tracking-tight">{me.tier_meta.name}{isStakeVip && <span className="ml-2 text-[11px] font-mono text-accent-mint">via stake</span>}</div>
                <div className="text-[12px] text-white/55 mt-0.5">
                  Voting power <span className="text-accent-violet tabular">{me.voting_power.total}</span>{' '}
                  {me.voting_power.bonus > 0 && <span className="text-white/40">(+{me.voting_power.bonus} from {me.voting_power.staked.toLocaleString()} VOLTZ staked)</span>}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3 flex-wrap">
              {exp && (
                <div className="text-right">
                  <div className="eyebrow">Renews</div>
                  <div className="text-sm tabular">{new Date(exp).toLocaleDateString()}</div>
                </div>
              )}
              {me.subscription && me.subscription.auto_renew !== false && (
                <button onClick={cancel} className="btn text-[12px]" data-testid="sub-cancel"><X size={12}/> Cancel</button>
              )}
              <Link to="/governance" className="btn btn-violet text-[12px]" data-testid="sub-gov-link">
                Governance <ChevronRight size={12}/>
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Tier cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {tiers.map((t) => {
          const I = TIER_ICONS[t.id];
          const isCurrent = currentTier === t.id;
          const isUpgrade = ['free','pro','vip'].indexOf(t.id) > ['free','pro','vip'].indexOf(currentTier);
          const ring = TIER_RING[t.id];
          const featured = t.id === 'pro';
          return (
            <div key={t.id} className={`bento ${ring} relative ${featured ? 'md:scale-[1.03]' : ''}`} data-testid={`tier-${t.id}`}>
              {featured && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-[10px] font-mono uppercase tracking-widest bg-accent-aurora/15 border border-accent-aurora/30 text-accent-aurora">
                  Most popular
                </div>
              )}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <I className={TIER_COLORS[t.id]} size={20}/>
                  <div className="font-display font-bold text-xl tracking-tight">{t.name}</div>
                </div>
                {isCurrent && <span className="text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full bg-accent-mint/15 border border-accent-mint/30 text-accent-mint">Current</span>}
              </div>

              <div className="mt-5 flex items-baseline gap-1.5">
                <span className={`font-display font-bold text-4xl tracking-[-0.04em] tabular ${t.id === 'vip' ? 'grad-gold' : t.id === 'pro' ? 'grad-aurora' : ''}`}>${t.price_cad.toFixed(2)}</span>
                {t.price_cad > 0 && <span className="text-white/50 text-sm">/ month</span>}
              </div>
              {t.price_rmr > 0 && (
                <div className="text-[12px] text-white/55 mt-1">or <span className="text-accent-gold tabular">{t.price_rmr.toLocaleString()} VOLTZ</span>/mo{t.min_stake_rmr > 0 ? ` · or stake ${t.min_stake_rmr.toLocaleString()}+` : ''}</div>
              )}

              <div className="mt-5 space-y-2.5">
                {t.features.map((f, i) => (
                  <div key={i} className="flex items-start gap-2.5 text-[13px] text-white/75">
                    <Check size={14} className={`${TIER_COLORS[t.id]} mt-0.5 flex-shrink-0`}/>
                    <span>{f}</span>
                  </div>
                ))}
              </div>

              {/* Stats */}
              <div className="mt-5 pt-4 border-t border-white/5 grid grid-cols-3 gap-2">
                <Mini label="Earn" value={`${t.earn_multiplier}x`}/>
                <Mini label="APY" value={`${t.staking_apy_max}%`}/>
                <Mini label="Votes" value={`${t.vote_power}`}/>
              </div>

              {/* CTA */}
              <div className="mt-5">
                {isCurrent ? (
                  <button className="btn w-full justify-center" disabled>Current Plan</button>
                ) : t.id === 'free' ? (
                  <button className="btn w-full justify-center" disabled>Default</button>
                ) : (
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => setConfirm({tier: t.id, method: 'stripe'})}
                      disabled={busy?.startsWith(t.id)}
                      className={`btn ${t.id === 'vip' ? 'btn-primary' : 'btn-aurora'} text-[12px] justify-center`}
                      data-testid={`sub-stripe-${t.id}`}>
                      Pay ${t.price_cad}
                    </button>
                    <button
                      onClick={() => setConfirm({tier: t.id, method: 'rmr'})}
                      disabled={busy?.startsWith(t.id)}
                      className="btn text-[12px] justify-center"
                      data-testid={`sub-rmr-${t.id}`}>
                      <Coins size={12}/> {t.price_rmr} VOLTZ
                    </button>
                  </div>
                )}
                {t.id === 'vip' && currentTier !== 'vip' && (
                  <div className="text-center text-[10px] text-white/45 mt-2">or <Link to="/wallet#stake" className="text-accent-mint hover:underline">stake {t.min_stake_rmr.toLocaleString()}+ VOLTZ</Link></div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* FAQ-lite */}
      <div className="bento">
        <div className="eyebrow mb-3">How it works</div>
        <div className="grid sm:grid-cols-3 gap-4 text-[13px] text-white/65">
          <div className="flex gap-2.5"><Zap size={16} className="text-accent-gold flex-shrink-0 mt-0.5"/><div><b className="text-white">Earn multiplier</b> applies instantly to every km you ride.</div></div>
          <div className="flex gap-2.5"><TrendingUp size={16} className="text-accent-mint flex-shrink-0 mt-0.5"/><div><b className="text-white">Higher APY tiers</b> unlock automatically when staking.</div></div>
          <div className="flex gap-2.5"><Crown size={16} className="text-accent-aurora flex-shrink-0 mt-0.5"/><div><b className="text-white">Vote</b> on protocol changes — add/remove vehicles, set parameters.</div></div>
        </div>
      </div>

      {/* Confirm modal */}
      {confirm && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md flex items-center justify-center p-4" onClick={() => setConfirm(null)}>
          <div className="glass-strong rounded-2xl p-6 max-w-sm w-full border border-white/10" onClick={e=>e.stopPropagation()}>
            <div className="flex items-center gap-2 mb-2">
              {(() => { const I = TIER_ICONS[confirm.tier]; return <I className={TIER_COLORS[confirm.tier]} size={20}/>; })()}
              <div className="font-display font-bold text-lg">Confirm {confirm.tier.toUpperCase()}</div>
            </div>
            <p className="text-[13px] text-white/65 mb-5">
              {confirm.method === 'rmr'
                ? <>You'll be charged <b className="text-accent-gold">{tiers.find(t=>t.id===confirm.tier)?.price_rmr} VOLTZ</b> from your in-app balance. 30-day access.</>
                : <>You'll be redirected to Stripe to pay <b className="text-accent-gold">${tiers.find(t=>t.id===confirm.tier)?.price_cad} CAD</b>. 30-day access.</>}
            </p>
            <div className="flex gap-2">
              <button onClick={() => setConfirm(null)} className="btn flex-1 justify-center">Cancel</button>
              <button onClick={() => subscribe(confirm.tier, confirm.method)} className="btn btn-primary flex-1 justify-center" data-testid="sub-confirm">
                Confirm <ArrowUpRight size={13}/>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Mini({ label, value }) {
  return (
    <div className="text-center">
      <div className="eyebrow !text-[9px] mb-0.5">{label}</div>
      <div className="font-display font-bold text-base tabular">{value}</div>
    </div>
  );
}
