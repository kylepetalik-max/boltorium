import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { toast } from 'sonner';

export default function AuthCallback() {
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const [status, setStatus] = useState('Authenticating');

  useEffect(() => {
    const handle = async () => {
      const hash = window.location.hash;
      const params = new URLSearchParams(hash.replace('#', ''));
      const sessionId = params.get('session_id');
      if (!sessionId) {
        toast.error('No session ID received');
        navigate('/');
        return;
      }
      try {
        setStatus('Exchanging credentials');
        const { data } = await api.post('/auth/session', { session_id: sessionId });
        if (data?.session_token) localStorage.setItem('rmr_session_token', data.session_token);
        setStatus('Loading profile');
        await refresh();
        toast.success(`Welcome, ${data.first_name || data.name || 'Rider'}!`);
        navigate('/dashboard');
      } catch (e) {
        toast.error(e?.response?.data?.detail || 'Login failed');
        navigate('/');
      }
    };
    handle();
  }, [navigate, refresh]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-6">
      <div className="cyber-spinner" />
      <p className="font-display text-lg gradient-text">{status}…</p>
    </div>
  );
}
