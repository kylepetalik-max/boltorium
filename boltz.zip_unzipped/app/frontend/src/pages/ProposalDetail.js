import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';
import {
  CheckCircle2, XCircle, AlertCircle, Clock, Crown, ChevronLeft,
  Vote, ThumbsUp, ThumbsDown, MinusCircle, Calendar, User as UserIcon
} from 'lucide-react';

const STATUS_META = {
  active:         { label: 'Voting open',    color: 'text-accent-aurora', icon: Clock },
  passed:         { label: 'Passed',         color: 'text-accent-mint',   icon: CheckCircle2 },
  failed:         { label: 'Rejected',       color: 'text-accent-rose',   icon: XCircle },
  failed_quorum:  { label: 'No quorum',      color: 'text-white/50',      icon: AlertCircle },
  executed:       { label: 'Executed',       color: 'text-accent-gold',   icon: Crown },
  draft:          { label: 'Draft',          color: 'text-white/50',      icon: Clock },
};

function TimeLeft({ end }) {
  const ms = new Date(end).getTime() - Date.now();
  if (ms <= 0) return <span>Ended</span>;
  const d = Math.floor(ms / 86400000);
  const h = Math.floor((ms % 86400000) / 3600000);
  const m = Math.floor((ms % 3600000) / 60000);
  return <span className="tabular">{d > 0 ? `${d}d ${h}h` : `${h}h ${m}m`}</span>;
}

export default function ProposalDetail() {
  const { proposal_id } = useParams();
  const { user, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [p, setP] = useState(null);
  const [me, setMe] = useState(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [pr, m] = await Promise.all([
        api.get(`/governance/proposals/${proposal_id}`),
        api.get('/subscriptions/me').catch(() => ({ data: null })),
      ]);
      setP(pr.data); setMe(m.data);
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [proposal_id]);

  const vote = async (choice) => {
    setBusy(true);
    try {
      await api.post(`/governance/proposals/${proposal_id}/vote`, { choice });
      toast.success(`Voted ${choice}`);
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
    finally { setBusy(false); }
  };

  const execute = async () => {
    if (!window.confirm('Execute this proposal? This will apply the change to the protocol.')) return;
    setBusy(true);
    try {
      const { data } = await api.post(`/admin/governance/proposals/${proposal_id}/execute`);
      toast.success('Proposal executed');
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
    finally { setBusy(false); }
  };

  const finalize = async () => {
    setBusy(true);
    try {
      await api.post(`/admin/governance/proposals/${proposal_id}/finalize`);
      toast.success('Finalized');
      load();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
    finally { setBusy(false); }
  };

  if (loading) return <div className="py-20 flex justify-center"><div className="cyber-spinner"/></div>;
  if (!p) return <div className="py-20 text-center text-white/55">Proposal not found <Link to="/governance" className="text-accent-aurora underline">back</Link></div>;

  const status = STATUS_META[p.status] || STATUS_META.draft;
  const I = status.icon;
  const yes = p.voting_power?.yes ?? 0;
  const no = p.voting_power?.no ?? 0;
  const abstain = p.voting_power?.abstain ?? 0;
  const total = (yes + no) || 1;
  const yesPct = (yes / total) * 100;
  const noPct = (no / total) * 100;
  const quorumPct = Math.min(100, ((p.voting_power?.total ?? 0) / (p.min_quorum || 10)) * 100);
  const passing = (yes / total) >= (p.pass_threshold || 0.6);
  const canVote = (me?.voting_power?.total ?? 0) > 0;
  const alreadyVoted = !!p.my_vote;
  const isActive = p.status === 'active';

  return (
    <div className="fade-in space-y-6 max-w-4xl">
      <Link to="/governance" className="inline-flex items-center gap-1 text-[13px] text-white/55 hover:text-white"><ChevronLeft size={14}/> All proposals</Link>

      {/* Header */}
      <div className="bento">
        <div className="flex items-center gap-2 flex-wrap mb-3">
          <span className="text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full bg-white/[0.04] border border-white/[0.08] text-white/60">{p.type_label}</span>
          <span className={`text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full bg-white/[0.04] border border-white/[0.08] ${status.color} inline-flex items-center gap-1`}>
            <I size={10}/> {status.label}
          </span>
        </div>
        <h1 className="font-display font-bold text-[2rem] sm:text-[2.5rem] tracking-[-0.03em] leading-[1.1]">{p.title}</h1>
        <div className="text-[12px] text-white/45 mt-3 inline-flex items-center gap-3">
          <span className="inline-flex items-center gap-1"><UserIcon size={11}/> {p.created_by_name}</span>
          <span>·</span>
          <span className="inline-flex items-center gap-1"><Calendar size={11}/> Created {new Date(p.created_at).toLocaleDateString()}</span>
          {isActive && <><span>·</span><span className="text-accent-aurora">Ends in <TimeLeft end={p.voting_ends_at}/></span></>}
        </div>
        <p className="text-white/70 text-[15px] leading-relaxed mt-5 whitespace-pre-wrap">{p.description}</p>

        {/* Metadata */}
        {p.metadata && Object.keys(p.metadata).length > 0 && (
          <div className="mt-5 pt-5 border-t border-white/[0.06]">
            <div className="eyebrow mb-3">Proposed change</div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {Object.entries(p.metadata).map(([k, v]) => (
                <div key={k} className="bg-white/[0.025] rounded-lg p-3 border border-white/[0.04]">
                  <div className="eyebrow !text-[9px]">{k.replace(/_/g, ' ')}</div>
                  <div className="text-sm tabular font-mono mt-1 truncate">{String(v)}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {p.execution_result && (
          <div className="mt-5 p-3 rounded-lg bg-accent-gold/5 border border-accent-gold/20">
            <div className="eyebrow !text-[9px] mb-1 text-accent-gold">Execution result</div>
            <pre className="font-mono text-[11px] text-white/75 whitespace-pre-wrap break-all">{JSON.stringify(p.execution_result, null, 2)}</pre>
          </div>
        )}
      </div>

      {/* Voting */}
      <div className="bento">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="eyebrow">Live results</div>
            <div className="font-display font-semibold text-lg tracking-tight mt-0.5">{p.voter_count || 0} voter{p.voter_count === 1 ? '' : 's'} · {p.voting_power?.total ?? 0} total power</div>
          </div>
          <div className={`text-[11px] px-2 py-1 rounded-full font-mono uppercase tracking-widest border ${passing ? 'text-accent-mint border-accent-mint/30 bg-accent-mint/5' : 'text-accent-rose border-accent-rose/30 bg-accent-rose/5'}`}>
            {passing ? 'On track to pass' : 'Below threshold'}
          </div>
        </div>

        {/* Bar */}
        <div className="h-3 rounded-full bg-white/[0.05] overflow-hidden flex mb-3">
          <div className="bg-accent-mint transition-all" style={{ width: `${yesPct}%` }}/>
          <div className="bg-accent-rose transition-all" style={{ width: `${noPct}%` }}/>
        </div>
        <div className="grid grid-cols-3 gap-3 mb-5">
          <Stat label="For" value={yes} pct={yesPct} color="text-accent-mint"/>
          <Stat label="Against" value={no} pct={noPct} color="text-accent-rose"/>
          <Stat label="Abstain" value={abstain} pct={(abstain/(p.voting_power?.total||1))*100} color="text-white/60"/>
        </div>

        {/* Quorum */}
        <div>
          <div className="flex items-center justify-between text-[11px] mb-1.5">
            <span className="text-white/55">Quorum progress</span>
            <span className="tabular text-white/70">{p.voting_power?.total ?? 0} / {p.min_quorum} · {quorumPct.toFixed(0)}%</span>
          </div>
          <div className="h-1.5 rounded-full bg-white/[0.05] overflow-hidden">
            <div className="h-full bg-accent-aurora" style={{ width: `${quorumPct}%` }}/>
          </div>
        </div>

        {/* Vote buttons */}
        {isActive && (
          <div className="mt-6 pt-5 border-t border-white/[0.06]">
            {alreadyVoted ? (
              <div className="flex items-center justify-between">
                <div className="text-[13px]">
                  You voted <span className={`font-semibold ${p.my_vote.choice === 'yes' ? 'text-accent-mint' : p.my_vote.choice === 'no' ? 'text-accent-rose' : 'text-white/70'}`}>{p.my_vote.choice}</span> with <span className="text-accent-violet tabular">{p.my_vote.voting_power}</span> power
                </div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-white/40">{new Date(p.my_vote.voted_at).toLocaleString()}</span>
              </div>
            ) : !canVote ? (
              <div className="flex items-center justify-between flex-wrap gap-3">
                <div className="text-[13px] text-white/65">You need <b className="text-accent-aurora">Pro</b> or <b className="text-accent-gold">VIP</b> to vote.</div>
                <Link to="/subscription" className="btn btn-violet text-[12px]" data-testid="prop-upgrade"><Crown size={13}/> Upgrade</Link>
              </div>
            ) : (
              <div>
                <div className="text-[12px] text-white/55 mb-3">Your vote will count <span className="text-accent-violet tabular">{me?.voting_power?.total}</span> power ({me?.voting_power?.tier} tier{me?.voting_power?.bonus > 0 ? ` + ${me.voting_power.bonus} stake bonus` : ''})</div>
                <div className="grid grid-cols-3 gap-2">
                  <button onClick={() => vote('yes')} disabled={busy} className="btn btn-mint justify-center" data-testid="vote-yes"><ThumbsUp size={14}/> For</button>
                  <button onClick={() => vote('no')} disabled={busy} className="btn justify-center" style={{ background: 'linear-gradient(180deg, rgba(244,114,182,0.18), rgba(244,114,182,0.06))', borderColor: 'rgba(244,114,182,0.35)', color: '#F472B6' }} data-testid="vote-no"><ThumbsDown size={14}/> Against</button>
                  <button onClick={() => vote('abstain')} disabled={busy} className="btn justify-center" data-testid="vote-abstain"><MinusCircle size={14}/> Abstain</button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Admin controls */}
        {isAdmin && (
          <div className="mt-5 pt-5 border-t border-white/[0.06] flex items-center justify-between">
            <div className="eyebrow">Admin</div>
            <div className="flex gap-2">
              {p.status === 'active' && <button onClick={finalize} disabled={busy} className="btn text-[12px]" data-testid="adm-finalize">Force finalize</button>}
              {p.status === 'passed' && <button onClick={execute} disabled={busy} className="btn btn-primary text-[12px]" data-testid="adm-execute"><Crown size={13}/> Execute</button>}
            </div>
          </div>
        )}
      </div>

      {/* Recent voters */}
      {(p.recent_votes?.length ?? 0) > 0 && (
        <div className="bento">
          <div className="eyebrow mb-3">Recent voters</div>
          <div className="space-y-1">
            {p.recent_votes.map(v => (
              <div key={v.vote_id} className="flex items-center gap-3 py-2 border-b border-white/[0.03] last:border-0">
                <div className="w-8 h-8 rounded-lg overflow-hidden bg-white/[0.04] border border-white/[0.06] flex items-center justify-center text-xs">
                  {v.voter_picture ? <img src={v.voter_picture} alt="" className="w-full h-full object-cover"/> : v.voter_name.slice(0,1)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm truncate">{v.voter_name}</div>
                  <div className="text-[11px] text-white/45">{new Date(v.voted_at).toLocaleString()} · {v.tier}</div>
                </div>
                <div className={`text-[11px] font-mono uppercase tracking-widest ${v.choice === 'yes' ? 'text-accent-mint' : v.choice === 'no' ? 'text-accent-rose' : 'text-white/55'}`}>{v.choice}</div>
                <div className="text-sm tabular text-accent-violet font-semibold w-12 text-right">+{v.voting_power}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, pct, color }) {
  return (
    <div className="text-center">
      <div className={`font-display font-bold text-2xl tabular tracking-tight ${color}`}>{value}</div>
      <div className="eyebrow mt-0.5">{label} · {pct.toFixed(0)}%</div>
    </div>
  );
}
