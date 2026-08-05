import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';
import {
  Users, Coins, Package, Target, FileText, Bot, Cpu, Leaf,
  Plus, Trash2, ShieldCheck, Crown, Award, Wand2, Search, Vote, CheckCircle2
} from 'lucide-react';

export default function Admin() {
  const { user, isAdmin, refresh } = useAuth();
  const [tab, setTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [supply, setSupply] = useState(null);
  const [solanaCfg, setSolanaCfg] = useState(null);

  // Users
  const [users, setUsers] = useState({ users: [], total: 0, page: 1, pages: 1 });
  const [userQ, setUserQ] = useState('');

  // Txs
  const [txs, setTxs] = useState({ transactions: [], total: 0, page: 1, pages: 1 });

  // Carbon admin
  const [carbonMonthly, setCarbonMonthly] = useState(null);

  // Governance admin
  const [govProposals, setGovProposals] = useState([]);
  const [govFilter, setGovFilter] = useState('active');

  // Mint/Burn
  const [mintUid, setMintUid] = useState('');
  const [mintAmt, setMintAmt] = useState('');
  const [mintReason, setMintReason] = useState('admin_mint');

  const [busy, setBusy] = useState(false);

  const loadOverview = async () => {
    try {
      const [s, sup, sc] = await Promise.all([
        api.get('/admin/stats'),
        api.get('/admin/rmr-supply'),
        api.get('/admin/solana-config'),
      ]);
      setStats(s.data); setSupply(sup.data); setSolanaCfg(sc.data);
    } catch { /* non-fatal */ }
  };

  const loadUsers = async (page = 1, q = userQ) => {
    try { const { data } = await api.get(`/admin/users?page=${page}&limit=20&search=${encodeURIComponent(q)}`); setUsers(data); } catch { /* non-fatal */ }
  };
  const loadTxs = async (page = 1) => {
    try { const { data } = await api.get(`/admin/transactions?page=${page}&limit=50`); setTxs(data); } catch { /* non-fatal */ }
  };
  const loadCarbon = async () => {
    try { const { data } = await api.get('/admin/carbon/monthly'); setCarbonMonthly(data); } catch { /* non-fatal */ }
  };
  const loadGovernance = async (status = govFilter) => {
    try {
      const { data } = await api.get(`/governance/proposals${status === 'all' ? '' : `?status=${status}`}`);
      setGovProposals(data);
    } catch { /* non-fatal */ }
  };
  const finalizeProposal = async (pid) => {
    try { await api.post(`/admin/governance/proposals/${pid}/finalize`); toast.success('Finalized'); loadGovernance(); }
    catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
  };
  const executeProposal = async (pid) => {
    if (!window.confirm('Execute this proposal? This applies the change to the protocol.')) return;
    try { await api.post(`/admin/governance/proposals/${pid}/execute`); toast.success('Executed'); loadGovernance(); }
    catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
  };

  useEffect(() => {
    if (!isAdmin) return;
    loadOverview();
    if (tab === 'users') loadUsers();
    if (tab === 'audit') loadTxs();
    if (tab === 'carbon') loadCarbon();
    if (tab === 'governance') loadGovernance();
  }, [tab, isAdmin]);

  useEffect(() => {
    if (tab === 'governance') loadGovernance(govFilter);
    // eslint-disable-next-line
  }, [govFilter]);

  if (!isAdmin) return (
    <div className="py-20 text-center">
      <ShieldCheck className="mx-auto text-neon-pink mb-3" size={40}/>
      <div className="font-display tracking-wider text-lg">Admin access only</div>
      <button onClick={async () => { try { await api.post('/admin/bootstrap'); await refresh(); toast.success('You are now admin'); } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }}} className="btn-neon btn-neon-pink mt-4" data-testid="bootstrap-admin">Bootstrap (first user only)</button>
    </div>
  );

  const mint = async () => {
    if (!mintAmt || +mintAmt <= 0) return toast.error('Amount required');
    setBusy(true);
    try {
      await api.post('/admin/mint-rmr', { user_id: mintUid || null, amount: +mintAmt, reason: mintReason });
      toast.success(`Minted ${mintAmt} VOLTZ`);
      setMintAmt('');
      loadOverview();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
    finally { setBusy(false); }
  };
  const burn = async (uid) => {
    const amt = parseFloat(prompt('Burn amount VOLTZ?', '10'));
    if (!amt) return;
    setBusy(true);
    try { await api.post('/admin/burn-rmr', { user_id: uid, amount: amt, reason: 'admin_burn' }); toast.success('Burned'); loadUsers(users.page); loadOverview(); }
    catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
    finally { setBusy(false); }
  };
  const promote = async (uid) => {
    try { await api.post(`/admin/make-admin/${uid}`); toast.success('Promoted'); loadUsers(users.page); }
    catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
  };
  const runDropship = async () => { try { await api.post('/admin/run-dropship-agent'); toast.success('Dropship agent running'); } catch (e) { toast.error('Failed'); }};
  const purgePoc = async () => {
    if (!confirm('Remove all POC/test users + their rides/transactions? This cannot be undone.')) return;
    try {
      const { data } = await api.post('/admin/purge-poc-users');
      toast.success(`Removed ${data.removed} POC user(s)`);
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
  };
  const setupSolana = async () => { try { await api.post('/admin/setup-solana'); toast.success('Solana setup running'); setTimeout(loadOverview, 5000); } catch (e) { toast.error('Failed'); }};
  const awardCarbon = async () => {
    if (!confirm('Award this month’s top eco-rider with 500 VOLTZ? This will mint on-chain if wallet linked.')) return;
    setBusy(true);
    try {
      const { data } = await api.post('/admin/carbon/award-winner', { reward_rmr: 500 });
      toast.success(`Awarded ${data.award.winner_name} — 500 VOLTZ (${data.award.sol_mode})`);
      loadCarbon();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
    finally { setBusy(false); }
  };

  const TABS = [
    { id: 'overview', label: 'Overview', icon: Cpu },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'rmr', label: 'VOLTZ Supply', icon: Coins },
    { id: 'audit', label: 'Audit Log', icon: FileText },
    { id: 'dropship', label: 'Dropship', icon: Bot },
    { id: 'solana', label: 'Solana', icon: Wand2 },
    { id: 'carbon', label: 'Carbon', icon: Leaf },
    { id: 'governance', label: 'Governance', icon: Vote },
  ];

  return (
    <div className="fade-in space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[11px] tracking-[0.3em] text-white/50">// ADMIN</div>
          <h1 className="font-display font-bold text-3xl sm:text-4xl mt-1 gradient-text">Mission Control</h1>
        </div>
        <div className="text-[11px] text-white/55">{user?.email}</div>
      </div>

      <div className="flex gap-2 overflow-x-auto no-scrollbar">
        {TABS.map(t => {
          const I = t.icon;
          return (
            <button key={t.id} onClick={() => setTab(t.id)} data-testid={`adm-tab-${t.id}`}
              className={`px-3 py-2 rounded-lg text-xs font-display tracking-wider uppercase inline-flex items-center gap-2 whitespace-nowrap ${tab === t.id ? 'bg-white/15 text-neon-pink' : 'bg-white/5 text-white/65'}`}>
              <I size={14}/> {t.label}
            </button>
          );
        })}
      </div>

      {/* OVERVIEW */}
      {tab === 'overview' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Bento label="Users" value={stats?.totalUsers ?? 0} color="text-neon-blue"/>
            <Bento label="Rides" value={stats?.totalRides ?? 0} color="text-neon-cyan"/>
            <Bento label="Distance km" value={(stats?.totalDistance ?? 0).toFixed(2)} color="text-neon-pink"/>
            <Bento label="VOLTZ distributed" value={(stats?.totalRmrDistributed ?? 0).toFixed(2)} color="text-neon-gold"/>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Bento label="Circulating" value={(supply?.totalCirculating ?? 0).toFixed(2)} color="text-neon-gold"/>
            <Bento label="Minted" value={(supply?.totalMinted ?? 0).toFixed(2)} color="text-neon-green"/>
            <Bento label="Burned" value={(supply?.totalBurned ?? 0).toFixed(2)} color="text-neon-pink"/>
            <Bento label="Earned (rewards)" value={(supply?.totalEarned ?? 0).toFixed(2)} color="text-neon-blue"/>
          </div>
        </div>
      )}

      {/* USERS */}
      {tab === 'users' && (
        <div className="space-y-3">
          <div className="flex gap-2 items-center bg-white/5 rounded-xl px-3 py-2 max-w-md">
            <Search size={14} className="text-white/60"/>
            <input className="bg-transparent flex-1 outline-none text-sm" placeholder="Search email or name" value={userQ} onChange={e => setUserQ(e.target.value)} onKeyDown={e => e.key === 'Enter' && loadUsers(1, userQ)} data-testid="adm-user-search"/>
            <button className="btn-neon btn-ghost text-xs" onClick={() => loadUsers(1, userQ)}>Find</button>
          </div>
          <div className="bento overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-[10px] tracking-widest text-white/55 uppercase"><th className="py-2">User</th><th>Email</th><th>VOLTZ</th><th>Level</th><th>Wallet</th><th>Admin</th><th></th></tr></thead>
              <tbody>
                {users.users.map(u => (
                  <tr key={u.user_id} className="border-t border-white/5">
                    <td className="py-2 pr-3">{u.first_name || ''} {u.last_name || ''}</td>
                    <td className="pr-3 text-white/70">{u.email}</td>
                    <td className="text-neon-gold pr-3">{u.rmr_balance?.toFixed(2)}</td>
                    <td className="pr-3">{u.level}</td>
                    <td className="font-mono text-[10px] text-white/60 pr-3">{u.wallet_address ? u.wallet_address.slice(0,8)+'…' : '—'}</td>
                    <td>{u.is_admin ? <Crown className="text-neon-gold" size={14}/> : ''}</td>
                    <td className="text-right">
                      <button onClick={() => promote(u.user_id)} className="btn-ghost btn-neon text-[10px] mr-1" data-testid={`promote-${u.user_id}`}><ShieldCheck size={11}/></button>
                      <button onClick={() => burn(u.user_id)} className="btn-ghost btn-neon text-[10px]" data-testid={`burn-${u.user_id}`}><Trash2 size={11}/></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="text-[11px] text-white/55 mt-3">Page {users.page} of {users.pages} • {users.total} users</div>
          </div>
        </div>
      )}

      {/* VOLTZ */}
      {tab === 'rmr' && (
        <div className="bento space-y-3">
          <div className="text-xs tracking-widest text-white/55 uppercase">Mint / Burn VOLTZ</div>
          <div className="grid sm:grid-cols-4 gap-2">
            <input className="input-cy" placeholder="User ID (blank=treasury)" value={mintUid} onChange={e => setMintUid(e.target.value)} data-testid="adm-mint-uid"/>
            <input className="input-cy" type="number" placeholder="Amount" value={mintAmt} onChange={e => setMintAmt(e.target.value)} data-testid="adm-mint-amt"/>
            <input className="input-cy" placeholder="Reason" value={mintReason} onChange={e => setMintReason(e.target.value)} data-testid="adm-mint-reason"/>
            <button onClick={mint} disabled={busy} className="btn-neon btn-neon-gold" data-testid="adm-mint-btn"><Plus size={14} className="mr-1"/> Mint</button>
          </div>
        </div>
      )}

      {/* AUDIT */}
      {tab === 'audit' && (
        <div className="bento overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-[10px] tracking-widest text-white/55 uppercase"><th className="py-2">Time</th><th>User</th><th>Type</th><th>Amount</th><th>Ref</th></tr></thead>
            <tbody>
              {txs.transactions.map(t => (
                <tr key={t.transaction_id} className="border-t border-white/5">
                  <td className="py-2 text-white/70 pr-3 text-xs">{new Date(t.created_at).toLocaleString()}</td>
                  <td className="font-mono text-[10px] pr-3">{t.user_id}</td>
                  <td className="pr-3">{t.type}</td>
                  <td className={`pr-3 font-display ${t.amount > 0 ? 'text-neon-green' : 'text-neon-pink'}`}>{t.amount > 0 ? '+' : ''}{t.amount.toFixed(2)}</td>
                  <td className="font-mono text-[10px] text-white/55">{t.reference_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="text-[11px] text-white/55 mt-3">{txs.total} transactions</div>
        </div>
      )}

      {/* DROPSHIP */}
      {tab === 'dropship' && (
        <div className="bento space-y-3">
          <div className="text-xs tracking-widest text-white/55 uppercase">AI Dropshipping Agent</div>
          <p className="text-sm text-white/70">Runs a GPT-powered agent that seeds the marketplace with realistic LEV products across 14 categories — with curated product images, accurate market pricing (USD/CAD/VOLTZ/SOL), and brand-correct specs. Takes about 2–3 minutes.</p>
          <div className="flex gap-2 flex-wrap">
            <button onClick={runDropship} className="btn-neon btn-neon-pink" data-testid="adm-dropship"><Bot size={14} className="mr-1"/> Run Agent</button>
            <button onClick={purgePoc} className="btn-neon btn-ghost" data-testid="adm-purge-poc"><Trash2 size={14} className="mr-1"/> Purge POC Test Users</button>
          </div>
          <div className="text-[11px] text-white/50">Purge button removes all `poc_*` seed users + their rides, transactions, sessions, awards. Useful before going to production.</div>
        </div>
      )}

      {/* SOLANA */}
      {tab === 'solana' && (
        <div className="bento space-y-3">
          <div className="text-xs tracking-widest text-white/55 uppercase">Solana Configuration</div>
          <div className="grid sm:grid-cols-2 gap-3">
            <Info k="Cluster" v={solanaCfg?.rpc_url}/>
            <Info k="Mode" v={solanaCfg?.status?.mode}/>
            <Info k="Mint Address" v={solanaCfg?.status?.mint_address || '(not set)'}/>
            <Info k="Has Private Key" v={solanaCfg?.has_private_key ? 'yes' : 'no'}/>
          </div>
          <button onClick={setupSolana} className="btn-neon btn-neon-blue" data-testid="adm-setup-solana"><Wand2 size={14} className="mr-1"/> Bootstrap Devnet (run setup_solana.py)</button>
        </div>
      )}

      {/* CARBON */}
      {tab === 'carbon' && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Bento label="Active eco-riders" value={carbonMonthly?.totals?.active_riders ?? 0} color="text-neon-green"/>
            <Bento label="Total CO₂ saved" value={(carbonMonthly?.totals?.saved_kg ?? 0).toFixed(2) + ' kg'} color="text-neon-blue"/>
            <Bento label="Distance" value={(carbonMonthly?.totals?.distance_km ?? 0).toFixed(2) + ' km'} color="text-neon-cyan"/>
            <Bento label="Trees equiv" value={carbonMonthly?.totals?.trees_equivalent ?? 0} color="text-neon-gold"/>
          </div>
          <div className="bento">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs tracking-widest text-white/55 uppercase">{carbonMonthly?.month?.label} — Eco Leaderboard</div>
              {carbonMonthly?.awarded ? (
                <div className="text-[11px] text-neon-green inline-flex items-center gap-1"><Award size={12}/> Awarded to {carbonMonthly.awarded.winner_name}</div>
              ) : (
                <button onClick={awardCarbon} disabled={busy} className="btn-neon btn-neon-gold text-xs" data-testid="adm-carbon-award"><Crown size={12} className="mr-1"/> Award Top Rider (+500 VOLTZ)</button>
              )}
            </div>
            <div className="divide-y divide-white/5">
              {(carbonMonthly?.leaderboard || []).slice(0, 25).map((r, i) => (
                <div key={r.user_id} className="py-2 flex items-center gap-3">
                  <div className="w-10 text-center font-display font-bold text-white/80">#{i+1}</div>
                  <div className="flex-1">
                    <div className="font-body text-sm">{r.name || `${r.first_name} ${r.last_name}`}</div>
                    <div className="text-[10px] text-white/55 font-mono">{r.wallet_address ? r.wallet_address.slice(0,16)+'…' : 'no wallet linked'}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-neon-green font-display font-bold text-sm">{r.saved_kg.toFixed(2)} kg</div>
                    <div className="text-[10px] text-white/55">{r.rides} rides</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* GOVERNANCE */}
      {tab === 'governance' && (
        <div className="space-y-4">
          <div className="bento">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs tracking-widest text-white/55 uppercase">Proposals</div>
              <div className="flex gap-1 bg-white/[0.03] p-1 rounded-lg">
                {['active','passed','executed','failed','failed_quorum','all'].map(f => (
                  <button key={f} onClick={() => setGovFilter(f)}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-medium ${govFilter === f ? 'bg-white/10 text-white' : 'text-white/55 hover:text-white'}`}>
                    {f.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>
            {govProposals.length === 0 ? (
              <div className="text-center py-10 text-white/45 text-sm">No proposals to show</div>
            ) : (
              <div className="space-y-2">
                {govProposals.map(p => {
                  const yes = p.voting_power?.yes ?? 0;
                  const no = p.voting_power?.no ?? 0;
                  const total = (yes + no) || 1;
                  const yesPct = (yes / total) * 100;
                  return (
                    <div key={p.proposal_id} className="flex flex-col sm:flex-row sm:items-center gap-3 p-3 rounded-xl bg-white/[0.025] border border-white/[0.04]">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap mb-1">
                          <span className="text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full bg-white/[0.04] border border-white/[0.08] text-white/60">{p.type_label}</span>
                          <span className={`text-[10px] font-mono uppercase tracking-widest ${p.status === 'passed' ? 'text-accent-mint' : p.status === 'failed' ? 'text-accent-rose' : p.status === 'executed' ? 'text-accent-gold' : 'text-accent-aurora'}`}>{p.status}</span>
                        </div>
                        <div className="text-sm font-semibold truncate">{p.title}</div>
                        <div className="text-[11px] text-white/45 mt-0.5">by {p.created_by_name} · {p.voter_count || 0} votes · {p.voting_power?.total ?? 0}/{p.min_quorum} power</div>
                      </div>
                      <div className="w-40 flex-shrink-0">
                        <div className="flex items-center justify-between text-[10px] mb-1">
                          <span className="text-accent-mint tabular">{yes}</span>
                          <span className="text-accent-rose tabular">{no}</span>
                        </div>
                        <div className="h-1.5 rounded-full bg-white/[0.05] overflow-hidden flex">
                          <div className="bg-accent-mint" style={{ width: `${yesPct}%` }}/>
                          <div className="bg-accent-rose" style={{ width: `${100-yesPct}%` }}/>
                        </div>
                      </div>
                      <div className="flex gap-1.5">
                        <Link to={`/governance/${p.proposal_id}`} className="btn text-[11px]" data-testid={`adm-prop-view-${p.proposal_id}`}>View</Link>
                        {p.status === 'active' && <button onClick={() => finalizeProposal(p.proposal_id)} className="btn text-[11px]" data-testid={`adm-prop-finalize-${p.proposal_id}`}>Finalize</button>}
                        {p.status === 'passed' && <button onClick={() => executeProposal(p.proposal_id)} className="btn btn-primary text-[11px]" data-testid={`adm-prop-execute-${p.proposal_id}`}><CheckCircle2 size={11}/> Execute</button>}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Bento({ label, value, color = 'text-white' }) {
  return (
    <div className="bento">
      <div className="text-[10px] tracking-widest text-white/55 uppercase">{label}</div>
      <div className={`font-display font-bold text-2xl mt-1 ${color}`}>{value}</div>
    </div>
  );
}
function Info({ k, v }) {
  return (
    <div className="bg-white/5 rounded-lg p-3"><div className="text-[10px] tracking-widest text-white/55 uppercase">{k}</div><div className="font-mono text-xs text-white/80 mt-1 break-all">{v ?? '—'}</div></div>
  );
}
