import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';
import { Bike, Save, User as UserIcon, Crown, Star, Shield, Zap, TrendingUp, Vote, ArrowUpRight } from 'lucide-react';

const VEHICLES = [
  { value: 'bicycle', label: 'Bicycle', co2: 0 },
  { value: 'skateboard', label: 'Skateboard', co2: 0 },
  { value: 'ebike', label: 'E-Bike', co2: 6 },
  { value: 'electric_skateboard', label: 'Electric Skateboard', co2: 5 },
  { value: 'onewheel', label: 'Onewheel', co2: 5 },
  { value: 'euc', label: 'Electric Unicycle', co2: 5 },
  { value: 'electric_dirt_bike', label: 'Electric Dirt Bike', co2: 12 },
  { value: 'dirt_bike', label: 'Dirt Bike (gas)', co2: 250 },
];

const TIER_ICONS = { free: Shield, pro: Star, vip: Crown };
const TIER_COLORS = { free: 'text-white/70', pro: 'text-accent-aurora', vip: 'text-accent-gold' };

export default function Profile() {
  const { user, refresh } = useAuth();
  const [first, setFirst] = useState('');
  const [last, setLast] = useState('');
  const [username, setUsername] = useState('');
  const [vehicle, setVehicle] = useState('ebike');
  const [saving, setSaving] = useState(false);
  const [sub, setSub] = useState(null);

  useEffect(() => {
    if (user) {
      setFirst(user.first_name || ''); setLast(user.last_name || '');
      setUsername(user.username || ''); setVehicle(user.vehicle_type || 'ebike');
    }
    api.get('/subscriptions/me').then(r => setSub(r.data)).catch(() => {});
  }, [user]);

  const save = async () => {
    setSaving(true);
    try {
      await api.patch('/rider/profile', { first_name: first, last_name: last, username, vehicle_type: vehicle });
      await refresh();
      toast.success('Profile updated');
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
    finally { setSaving(false); }
  };

  const tier = sub?.tier || 'free';
  const tierMeta = sub?.tier_meta;
  const TierIcon = TIER_ICONS[tier];
  const vp = sub?.voting_power;

  return (
    <div className="fade-in space-y-6 max-w-4xl">
      <div>
        <div className="eyebrow">Profile</div>
        <h1 className="font-display font-bold text-[2.25rem] sm:text-[2.75rem] mt-1.5 tracking-[-0.03em] leading-[1.05] grad-headline">Your Rider Profile</h1>
      </div>

      <div className="bento">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-xl overflow-hidden flex items-center justify-center bg-white/[0.04] border border-white/[0.08]">
            {user?.picture ? <img src={user.picture} alt="u" className="w-full h-full object-cover"/> : <UserIcon size={28} className="text-accent-aurora"/>}
          </div>
          <div className="flex-1">
            <div className="font-display font-bold text-xl tracking-tight">{user?.name || user?.email}</div>
            <div className="text-white/55 text-sm">{user?.email}</div>
          </div>
          {TierIcon && (
            <div className="text-right">
              <div className="eyebrow">Member tier</div>
              <div className={`inline-flex items-center gap-1.5 mt-1 ${TIER_COLORS[tier]}`}>
                <TierIcon size={16}/> <span className="font-display font-bold text-base uppercase">{tier}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Active Tier Perks */}
      {tierMeta && (
        <div className={`bento relative overflow-hidden ${tier === 'vip' ? 'ring-gold' : tier === 'pro' ? 'ring-aurora' : ''}`}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="eyebrow">Active perks</div>
              <div className="font-display font-semibold text-lg tracking-tight mt-0.5">{tierMeta.name} membership</div>
            </div>
            <Link to="/subscription" className="btn text-[12px]" data-testid="profile-manage-sub">
              {tier === 'free' ? 'Upgrade' : 'Manage'} <ArrowUpRight size={12}/>
            </Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <PerkCard icon={Zap} label="VOLTZ multiplier" value={`${tierMeta.earn_multiplier}x`} color="text-accent-gold"/>
            <PerkCard icon={TrendingUp} label="Max APY" value={`${tierMeta.staking_apy_max}%`} color="text-accent-mint"/>
            <PerkCard icon={Vote} label="Voting power" value={vp?.total ?? tierMeta.vote_power} color="text-accent-violet"
                      sub={vp?.bonus > 0 ? `${tierMeta.vote_power} base + ${vp.bonus} stake` : null}/>
            <PerkCard icon={Crown} label="Can propose" value={tierMeta.can_propose ? 'Yes' : 'No'} color={tierMeta.can_propose ? 'text-accent-gold' : 'text-white/55'}/>
          </div>
        </div>
      )}

      <div className="bento space-y-4">
        <div className="text-xs tracking-widest text-white/50 uppercase">Edit Profile</div>
        <div className="grid sm:grid-cols-2 gap-3">
          <div>
            <label className="text-[11px] tracking-widest text-white/60 uppercase">First Name</label>
            <input data-testid="profile-first" className="input-cy mt-1" value={first} onChange={(e) => setFirst(e.target.value)} />
          </div>
          <div>
            <label className="text-[11px] tracking-widest text-white/60 uppercase">Last Name</label>
            <input data-testid="profile-last" className="input-cy mt-1" value={last} onChange={(e) => setLast(e.target.value)} />
          </div>
          <div className="sm:col-span-2">
            <label className="text-[11px] tracking-widest text-white/60 uppercase">Username</label>
            <input data-testid="profile-username" className="input-cy mt-1" value={username} onChange={(e) => setUsername(e.target.value)} />
          </div>
        </div>
        <div>
          <label className="text-[11px] tracking-widest text-white/60 uppercase mb-2 block">Primary Vehicle</label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {VEHICLES.map(v => (
              <button key={v.value} onClick={() => setVehicle(v.value)} data-testid={`vehicle-${v.value}`}
                className={`bento p-3 text-left transition ${vehicle === v.value ? 'neon-border-blue' : ''}`}>
                <Bike size={16} className="text-neon-blue"/>
                <div className="font-display tracking-wide text-sm mt-1">{v.label}</div>
                <div className="text-[10px] text-white/45">CO₂ {v.co2} g/km</div>
              </button>
            ))}
          </div>
        </div>
        <button onClick={save} disabled={saving} className="btn btn-aurora" data-testid="profile-save">
          <Save size={14} className="mr-2"/>{saving ? 'Saving…' : 'Save Profile'}
        </button>
      </div>
    </div>
  );
}

function PerkCard({ icon: I, label, value, color, sub }) {
  return (
    <div className="bg-white/[0.025] rounded-lg p-3 border border-white/[0.04]">
      <I className={color} size={15} strokeWidth={1.8}/>
      <div className={`font-display font-bold text-xl tabular tracking-tight mt-2 ${color}`}>{value}</div>
      <div className="eyebrow mt-0.5">{label}</div>
      {sub && <div className="text-[10px] text-white/40 mt-0.5">{sub}</div>}
    </div>
  );
}
