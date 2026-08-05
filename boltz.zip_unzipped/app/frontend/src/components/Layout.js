import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import {
  LayoutDashboard, Bike, Gift, Target, ShoppingBag, Wallet,
  Trophy, User as UserIcon, Award, Leaf, Shield, Menu, X, LogOut, ChevronDown,
  Vote, Crown, Star
} from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import api from '@/lib/api';

const NAV = [
  { to: '/dashboard',    label: 'Overview',     icon: LayoutDashboard },
  { to: '/ride',         label: 'Ride',         icon: Bike },
  { to: '/airdrops',     label: 'Airdrops',     icon: Gift },
  { to: '/challenges',   label: 'Quests',       icon: Target },
  { to: '/marketplace',  label: 'Shop',         icon: ShoppingBag },
  { to: '/wallet',       label: 'Wallet',       icon: Wallet },
  { to: '/governance',   label: 'Vote',         icon: Vote },
  { to: '/leaderboard',  label: 'Leaders',      icon: Trophy },
  { to: '/carbon',       label: 'Carbon',       icon: Leaf },
];

export default function Layout() {
  const { user, isAdmin, logout } = useAuth();
  const loc = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [tier, setTier] = useState('free');
  const menuRef = useRef(null);

  useEffect(() => {
    const handler = (e) => { if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false); };
    if (menuOpen) document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [menuOpen]);

  useEffect(() => {
    api.get('/subscriptions/me').then(r => setTier(r.data?.tier || 'free')).catch(() => {});
  }, [user?.user_id]);

  const initials = (user?.name || user?.first_name || user?.email || 'R').slice(0, 2).toUpperCase();
  const TierIcon = tier === 'vip' ? Crown : tier === 'pro' ? Star : null;
  const tierColor = tier === 'vip' ? 'text-accent-gold' : tier === 'pro' ? 'text-accent-aurora' : 'text-white/50';

  return (
    <div className="min-h-screen">
      {/* Top Nav */}
      <header className="sticky top-0 z-40 glass-strong border-b border-white/[0.06]">
        <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          <Link to="/dashboard" className="flex items-center gap-2.5 group" data-testid="nav-logo">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center font-display font-bold text-base"
                 style={{ background: 'linear-gradient(135deg, #F5C842 0%, #E8A700 100%)', color: '#1a1100', boxShadow: '0 0 0 1px rgba(255,255,255,0.1) inset, 0 8px 20px -8px rgba(245,200,66,0.5)' }}>
              R
            </div>
            <div className="hidden sm:block leading-tight">
              <div className="font-display font-bold text-[15px] tracking-tight">VOLTZ</div>
              <div className="text-[10px] tracking-[0.18em] text-white/45 uppercase font-mono">Ride to Earn</div>
            </div>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden lg:flex items-center gap-1">
            {NAV.map((it) => {
              const Active = loc.pathname === it.to;
              const Icon = it.icon;
              return (
                <Link key={it.to} to={it.to} data-testid={`nav-${it.label.toLowerCase()}`}
                  className={`px-3 py-2 rounded-lg text-[13px] font-medium inline-flex items-center gap-2 transition-all duration-200 ${Active ? 'bg-white/[0.06] text-white' : 'text-white/55 hover:text-white hover:bg-white/[0.04]'}`}>
                  <Icon size={15} strokeWidth={Active ? 2.2 : 1.8} />
                  {it.label}
                </Link>
              );
            })}
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-2">
            {/* VOLTZ Balance pill */}
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-xl ring-gold tabular" data-testid="nav-rmr-balance"
                 style={{ background: 'linear-gradient(180deg, rgba(245,200,66,0.08), rgba(245,200,66,0.02))' }}>
              <span className="text-accent-gold font-semibold text-sm">{(user?.rmr_balance ?? 0).toFixed(2)}</span>
              <span className="text-[10px] font-mono tracking-wider text-white/45">VOLTZ</span>
            </div>

            {/* Profile menu */}
            <div className="relative" ref={menuRef}>
              <button onClick={() => setMenuOpen(!menuOpen)} className="flex items-center gap-1.5 p-1 pr-2 rounded-xl hover:bg-white/5 transition-colors" data-testid="nav-profile">
                <div className="w-8 h-8 rounded-lg overflow-hidden bg-white/[0.04] border border-white/10 flex items-center justify-center text-xs font-semibold relative">
                  {user?.picture ? <img src={user.picture} alt="u" className="w-full h-full object-cover" /> : initials}
                  {TierIcon && (
                    <span className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-bg-base flex items-center justify-center ${tierColor}`} style={{ background: '#07080d' }}>
                      <TierIcon size={9} strokeWidth={2.4}/>
                    </span>
                  )}
                </div>
                <ChevronDown size={14} className="text-white/50" />
              </button>
              {menuOpen && (
                <div className="absolute right-0 top-full mt-2 w-64 glass-strong rounded-2xl border border-white/[0.08] shadow-xl overflow-hidden">
                  <div className="px-4 py-3 border-b border-white/5">
                    <div className="text-sm font-semibold truncate">{user?.name || user?.first_name || 'Rider'}</div>
                    <div className="text-[11px] text-white/50 truncate">{user?.email}</div>
                    <div className="mt-2 inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-white/[0.04] border border-white/10">
                      {TierIcon && <TierIcon size={11} className={tierColor}/>}
                      <span className={`text-[10px] font-mono uppercase tracking-widest ${tierColor}`}>{tier}</span>
                    </div>
                  </div>
                  <button onClick={() => { setMenuOpen(false); navigate('/profile'); }} className="w-full text-left px-4 py-2.5 text-sm hover:bg-white/5 flex items-center gap-2"><UserIcon size={14}/> Profile</button>
                  <button onClick={() => { setMenuOpen(false); navigate('/subscription'); }} className="w-full text-left px-4 py-2.5 text-sm hover:bg-white/5 flex items-center gap-2" data-testid="nav-subscription">
                    <Crown size={14} className="text-accent-gold"/>{' '}
                    {tier === 'free' ? <>Upgrade <span className="ml-auto text-[10px] text-accent-gold">PRO/VIP</span></> : <>Manage subscription</>}
                  </button>
                  <button onClick={() => { setMenuOpen(false); navigate('/governance'); }} className="w-full text-left px-4 py-2.5 text-sm hover:bg-white/5 flex items-center gap-2"><Vote size={14}/> Governance</button>
                  <button onClick={() => { setMenuOpen(false); navigate('/achievements'); }} className="w-full text-left px-4 py-2.5 text-sm hover:bg-white/5 flex items-center gap-2"><Award size={14}/> Achievements</button>
                  {isAdmin && <button onClick={() => { setMenuOpen(false); navigate('/admin'); }} className="w-full text-left px-4 py-2.5 text-sm hover:bg-white/5 flex items-center gap-2 text-accent-violet" data-testid="nav-admin"><Shield size={14}/> Admin</button>}
                  <button onClick={() => { setMenuOpen(false); logout(); }} className="w-full text-left px-4 py-2.5 text-sm hover:bg-white/5 flex items-center gap-2 text-white/70" data-testid="nav-logout"><LogOut size={14}/> Sign out</button>
                </div>
              )}
            </div>

            <button className="lg:hidden p-2 rounded-xl hover:bg-white/5" onClick={() => setOpen(!open)} data-testid="nav-toggle">
              {open ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </header>

      {/* Mobile drawer */}
      {open && (
        <div className="lg:hidden fixed inset-0 z-50 bg-black/70 backdrop-blur-md" onClick={() => setOpen(false)}>
          <div className="absolute right-0 top-0 bottom-0 w-72 glass-strong p-4 overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-5">
              <div className="font-display font-bold text-base">Menu</div>
              <button onClick={() => setOpen(false)} className="p-2"><X size={18}/></button>
            </div>
            <nav className="flex flex-col gap-0.5">
              {NAV.map((it) => {
                const Icon = it.icon;
                const Active = loc.pathname === it.to;
                return (
                  <Link key={it.to} to={it.to} onClick={() => setOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium ${Active ? 'bg-white/8 text-white' : 'text-white/70 hover:bg-white/5'}`}>
                    <Icon size={17} /> {it.label}
                  </Link>
                );
              })}
              <div className="my-2 h-px bg-white/5"/>
              <Link to="/profile" onClick={() => setOpen(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-white/70 hover:bg-white/5"><UserIcon size={17}/> Profile</Link>
              <Link to="/subscription" onClick={() => setOpen(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-white/70 hover:bg-white/5"><Crown size={17} className="text-accent-gold"/> Subscription</Link>
              <Link to="/achievements" onClick={() => setOpen(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-white/70 hover:bg-white/5"><Award size={17}/> Achievements</Link>
              {isAdmin && <Link to="/admin" onClick={() => setOpen(false)} className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-accent-violet hover:bg-white/5"><Shield size={17}/> Admin</Link>}
              <button onClick={() => { setOpen(false); logout(); }} className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-white/70 hover:bg-white/5"><LogOut size={17}/> Sign out</button>
            </nav>
          </div>
        </div>
      )}

      <main className="max-w-screen-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
        <Outlet />
      </main>
    </div>
  );
}
