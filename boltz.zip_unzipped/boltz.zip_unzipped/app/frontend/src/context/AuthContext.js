import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import api from '@/lib/api';

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get('/auth/me');
      setUser(data);
      try {
        const adm = await api.get('/admin/check');
        setIsAdmin(adm.data?.isAdmin || false);
      } catch { setIsAdmin(false); }
    } catch {
      setUser(null);
      setIsAdmin(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const login = () => {
    const redirect = `${window.location.origin}/auth/callback`;
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirect)}`;
  };

  const logout = async () => {
    try { await api.post('/auth/logout'); } catch {}
    localStorage.removeItem('rmr_session_token');
    setUser(null);
    setIsAdmin(false);
    window.location.href = '/';
  };

  return (
    <AuthCtx.Provider value={{ user, loading, isAdmin, refresh, login, logout, setUser }}>
      {children}
    </AuthCtx.Provider>
  );
}

export const useAuth = () => useContext(AuthCtx);
