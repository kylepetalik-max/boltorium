import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Toaster } from 'sonner';
import '@/App.css';
import { AuthProvider, useAuth } from '@/context/AuthContext';
import Layout from '@/components/Layout';
import Landing from '@/pages/Landing';
import AuthCallback from '@/pages/AuthCallback';
import Dashboard from '@/pages/Dashboard';
import Ride from '@/pages/Ride';
import Airdrops from '@/pages/Airdrops';
import Challenges from '@/pages/Challenges';
import Marketplace from '@/pages/Marketplace';
import Wallet from '@/pages/Wallet';
import Leaderboard from '@/pages/Leaderboard';
import Profile from '@/pages/Profile';
import Achievements from '@/pages/Achievements';
import Carbon from '@/pages/Carbon';
import Subscription from '@/pages/Subscription';
import Governance from '@/pages/Governance';
import ProposalDetail from '@/pages/ProposalDetail';
import Admin from '@/pages/Admin';

function Protected({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="cyber-spinner" />
      </div>
    );
  }
  if (!user) return <Navigate to="/" replace state={{ from: location }} />;
  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster position="top-right" theme="dark" richColors closeButton />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route element={<Protected><Layout /></Protected>}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/ride" element={<Ride />} />
            <Route path="/airdrops" element={<Airdrops />} />
            <Route path="/challenges" element={<Challenges />} />
            <Route path="/marketplace" element={<Marketplace />} />
            <Route path="/wallet" element={<Wallet />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/achievements" element={<Achievements />} />
            <Route path="/carbon" element={<Carbon />} />
            <Route path="/subscription" element={<Subscription />} />
            <Route path="/governance" element={<Governance />} />
            <Route path="/governance/:proposal_id" element={<ProposalDetail />} />
            <Route path="/admin" element={<Admin />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
