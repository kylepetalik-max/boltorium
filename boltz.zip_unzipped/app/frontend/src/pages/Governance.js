import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';
import {
  Vote, Plus, Filter, CheckCircle2, XCircle, AlertCircle, Clock,
  Crown, ChevronRight, Sparkles, Zap, X, Calendar
} from 'lucide-react';

const STATUS_META = {
  active:         { label: 'Active',          color: 'text-accent-aurora', bg: 'bg-accent-aurora/10 border-accent-aurora/25', icon: Clock },
  passed:         { label: 'Passed',          color: 'text-accent-mint',   bg: 'bg-accent-mint/10 border-accent-mint/25',     icon: CheckCircle2 },
  failed:         { label: 'Rejected',        color: 'text-accent-rose',   bg: 'bg-accent-rose/10 border-accent-rose/25',     icon: XCircle },
  failed_quorum:  { label: 'No quorum',       color: 'text-white/50',      bg: 'bg-white/[0.04] border-white/10',             icon: AlertCircle },
  executed:       { label: 'Executed',        color: 'text-accent-gold',   bg: 'bg-accent-gold/10 border-accent-gold/25',     icon: Crown },
  draft:          { label: 'Draft',           color: 'text-white/50',      bg: 'bg-white/[0.04] border-white/10',             icon: Clock },
};

const FILTERS = [
  { id: 'all',      label: 'All' },
  { id: 'active',   label: 'Active' },
  { id: 'passed',   label: 'Passed' },
  { id: 'executed', label: 'Executed' },
  { id: 'failed',   label: 'Rejected' },
];

function TypeBadge({ type }) {
  const labels = {
    vehicle_add: 'Add vehicle',
    vehicle_remove: 'Remove vehicle',
    parameter_change: 'Parameter',
    feature_request: 'Feature',
    treasury: 'Treasury',
    community: 'Community',
  };
  return <span className="text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full bg-white/[0.04] border border-white/[0.08] text-white/60">{labels[type] || type}</span>;
}

function TimeLeft({ end }) {
  const ms = new Date(end).getTime() - Date.now();
  if (ms <= 0) return <span className="text-white/40">ended</span>;
  const d = Math.floor(ms / 86400000);
  const h = Math.floor((ms % 86400000) / 3600000);
  return <span className="text-accent-aurora tabular">{d > 0 ? `${d}d ${h}h` : `${h}h ${Math.floor((ms%3600000)/60000)}m`} left</span>;
}

export default function Governance() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState('active');
  const [proposals, setProposals] = useState([]);
  const [config, setConfig] = useState(null);
  const [myGov, setMyGov] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [p, c, m] = await Promise.all([
        api.get(`/governance/proposals${tab === 'all' ? '' : `?status=${tab}`}`),
        api.get('/governance/config'),
        api.get('/governance/me').catch(() => ({ data: null })),
      ]);
      setProposals(p.data); setConfig(c.data); setMyGov(m.data);
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, [tab]);

  const canPropose = myGov?.voting_power?.tier === 'vip';
  const myPower = myGov?.voting_power?.total ?? 0;

  return (
    <div className="fade-in space-y-7">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <div className="eyebrow">Protocol Governance</div>
          <h1 className="font-display font-bold text-[2.25rem] sm:text-[2.75rem] mt-1.5 tracking-[-0.03em] leading-[1.05]">
            <span className="grad-headline">Shape the protocol.</span>{' '}
            <span className="grad-aurora">Cast your vote.</span>
          </h1>
          <p className="text-white/55 mt-2 text-[14px] max-w-2xl">VIP holders propose changes — vehicles, parameters, treasury. Pro and VIP holders vote. Passed proposals are executed by admin within 24h.</p>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/subscription" className="btn text-[12px]" data-testid="gov-tier-link">Your tier <ChevronRight size={12}/></Link>
          {canPropose ? (
            <button onClick={() => setShowCreate(true)} className="btn btn-primary" data-testid="gov-create"><Plus size={14}/> New proposal</button>
          ) : (
            <Link to="/subscription" className="btn btn-violet" data-testid="gov-upgrade"><Crown size={14}/> Upgrade to propose</Link>
          )}
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bento">
          <div className="eyebrow">Your tier</div>
          <div className="font-display font-bold text-2xl tracking-tight mt-1.5 capitalize">{myGov?.voting_power?.tier || 'free'}</div>
        </div>
        <div className="bento">
          <div className="eyebrow">Voting power</div>
          <div className="font-display font-bold text-2xl text-accent-violet tabular tracking-tight mt-1.5">{myPower}</div>
        </div>
        <div className="bento">
          <div className="eyebrow">Quorum</div>
          <div className="font-display font-bold text-2xl text-accent-aurora tabular tracking-tight mt-1.5">{config?.quorum ?? '—'}</div>
        </div>
        <div className="bento">
          <div className="eyebrow">Threshold</div>
          <div className="font-display font-bold text-2xl text-accent-mint tabular tracking-tight mt-1.5">{((config?.threshold ?? 0.6) * 100).toFixed(0)}%</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
        <Filter size={14} className="text-white/40 mr-1"/>
        {FILTERS.map(f => (
          <button key={f.id} onClick={() => setTab(f.id)} data-testid={`gov-filter-${f.id}`}
            className={`px-3 py-1.5 rounded-full text-[12px] font-medium whitespace-nowrap transition-colors ${tab === f.id ? 'bg-white/[0.08] text-white' : 'bg-white/[0.03] text-white/55 hover:text-white'}`}>
            {f.label}
          </button>
        ))}
      </div>

      {/* Proposals list */}
      {loading ? (
        <div className="py-20 flex justify-center"><div className="cyber-spinner"/></div>
      ) : proposals.length === 0 ? (
        <div className="bento text-center py-14">
          <Sparkles className="mx-auto text-white/30 mb-2" size={22}/>
          <div className="text-white/60 text-sm">No {tab === 'all' ? '' : tab} proposals yet</div>
          {canPropose && <button onClick={() => setShowCreate(true)} className="btn btn-primary mt-4" data-testid="gov-create-empty"><Plus size={14}/> Create the first proposal</button>}
        </div>
      ) : (
        <div className="space-y-3">
          {proposals.map(p => <ProposalRow key={p.proposal_id} p={p} navigate={navigate} />)}
        </div>
      )}

      {showCreate && <CreateModal onClose={() => setShowCreate(false)} onCreated={() => { setShowCreate(false); load(); }} config={config}/>}
    </div>
  );
}

function ProposalRow({ p, navigate }) {
  const meta = STATUS_META[p.status] || STATUS_META.draft;
  const I = meta.icon;
  const yes = p.voting_power?.yes ?? 0;
  const no = p.voting_power?.no ?? 0;
  const total = (yes + no) || 1;
  const yesPct = (yes / total) * 100;
  const quorumPct = Math.min(100, ((p.voting_power?.total ?? 0) / (p.min_quorum || 10)) * 100);

  return (
    <button onClick={() => navigate(`/governance/${p.proposal_id}`)} className="bento w-full text-left group" data-testid={`prop-${p.proposal_id}`}>
      <div className="flex flex-col sm:flex-row sm:items-start gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <TypeBadge type={p.type}/>
            <span className={`text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full border ${meta.bg} ${meta.color} inline-flex items-center gap-1`}>
              <I size={10}/> {meta.label}
            </span>
            {p.my_vote && <span className="text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full bg-accent-violet/10 border border-accent-violet/25 text-accent-violet">voted {p.my_vote.choice}</span>}
          </div>
          <div className="font-display font-semibold text-[17px] tracking-tight">{p.title}</div>
          <div className="text-[12px] text-white/50 mt-1 line-clamp-2">{p.description}</div>
          <div className="text-[11px] text-white/40 mt-2 inline-flex items-center gap-3">
            <span>by {p.created_by_name}</span>
            <span>·</span>
            <span className="inline-flex items-center gap-1"><Calendar size={10}/> <TimeLeft end={p.voting_ends_at}/></span>
          </div>
        </div>
        <div className="sm:w-64 flex-shrink-0">
          <div className="flex items-center justify-between text-[11px] mb-1">
            <span className="text-accent-mint tabular">{yes} for</span>
            <span className="text-accent-rose tabular">{no} against</span>
          </div>
          <div className="h-2 rounded-full bg-white/[0.05] overflow-hidden flex">
            <div className="bg-accent-mint" style={{ width: `${yesPct}%` }}/>
            <div className="bg-accent-rose" style={{ width: `${100-yesPct}%` }}/>
          </div>
          <div className="flex items-center justify-between text-[10px] text-white/40 mt-2">
            <span>{p.voter_count || 0} voters</span>
            <span className="tabular">Quorum {Math.min(quorumPct, 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>
    </button>
  );
}

function CreateModal({ onClose, onCreated, config }) {
  const [type, setType] = useState('vehicle_add');
  const [title, setTitle] = useState('');
  const [desc, setDesc] = useState('');
  const [duration, setDuration] = useState(7);
  const [vehicleId, setVehicleId] = useState('');
  const [vehicleLabel, setVehicleLabel] = useState('');
  const [gPerKm, setGPerKm] = useState(8);
  const [paramKey, setParamKey] = useState('');
  const [paramValue, setParamValue] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (title.length < 4 || desc.length < 10) return toast.error('Title and description must be longer');
    setBusy(true);
    let metadata = {};
    if (type === 'vehicle_add') metadata = { vehicle_id: vehicleId.trim().toLowerCase().replace(/\s+/g, '_'), label: vehicleLabel || vehicleId, g_per_km: Number(gPerKm) };
    else if (type === 'vehicle_remove') metadata = { vehicle_id: vehicleId.trim().toLowerCase() };
    else if (type === 'parameter_change') metadata = { key: paramKey, value: paramValue };
    try {
      await api.post('/governance/proposals', { type, title, description: desc, duration_days: Number(duration), metadata });
      toast.success('Proposal created');
      onCreated();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
    finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md flex items-center justify-center p-4 overflow-auto" onClick={onClose}>
      <div className="glass-strong rounded-2xl p-6 max-w-lg w-full border border-white/10 my-8" onClick={e=>e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <div className="font-display font-bold text-xl tracking-tight">New proposal</div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-white/5"><X size={18}/></button>
        </div>
        <div className="space-y-4">
          <Field label="Type">
            <select className="input-cy" value={type} onChange={e => setType(e.target.value)} data-testid="prop-type">
              {config?.proposal_types?.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
            </select>
          </Field>
          <Field label="Title">
            <input className="input-cy" value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Add Hoverboard support" data-testid="prop-title"/>
          </Field>
          <Field label="Description">
            <textarea className="input-cy min-h-[110px] resize-none" value={desc} onChange={e => setDesc(e.target.value)} placeholder="Why should this pass? Provide context, data, and expected impact." data-testid="prop-desc"/>
          </Field>

          {type === 'vehicle_add' && (
            <div className="grid grid-cols-2 gap-2">
              <Field label="Vehicle ID (slug)"><input className="input-cy" value={vehicleId} onChange={e=>setVehicleId(e.target.value)} placeholder="hoverboard" data-testid="prop-vehicle-id"/></Field>
              <Field label="Display name"><input className="input-cy" value={vehicleLabel} onChange={e=>setVehicleLabel(e.target.value)} placeholder="Hoverboard"/></Field>
              <Field label="CO₂ g / km"><input type="number" className="input-cy" value={gPerKm} onChange={e=>setGPerKm(e.target.value)} placeholder="8"/></Field>
            </div>
          )}
          {type === 'vehicle_remove' && (
            <Field label="Vehicle ID to remove"><input className="input-cy" value={vehicleId} onChange={e=>setVehicleId(e.target.value)} placeholder="dirt_bike"/></Field>
          )}
          {type === 'parameter_change' && (
            <div className="grid grid-cols-2 gap-2">
              <Field label="Parameter key"><input className="input-cy" value={paramKey} onChange={e=>setParamKey(e.target.value)} placeholder="rmr_per_km"/></Field>
              <Field label="New value"><input className="input-cy" value={paramValue} onChange={e=>setParamValue(e.target.value)} placeholder="1.5"/></Field>
            </div>
          )}

          <Field label="Voting duration">
            <div className="flex gap-2">
              {[3, 7, 14].map(d => (
                <button key={d} onClick={() => setDuration(d)} className={`flex-1 px-3 py-2 rounded-lg text-[12px] border ${duration === d ? 'bg-white/[0.08] border-white/20' : 'bg-white/[0.03] border-white/[0.06] text-white/55'}`}>{d} days</button>
              ))}
            </div>
          </Field>

          <div className="flex gap-2 pt-2">
            <button onClick={onClose} className="btn flex-1 justify-center">Cancel</button>
            <button onClick={submit} disabled={busy} className="btn btn-primary flex-1 justify-center" data-testid="prop-submit">
              {busy ? 'Submitting…' : <>Submit <Zap size={13}/></>}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return <div><label className="eyebrow block mb-1.5">{label}</label>{children}</div>;
}
