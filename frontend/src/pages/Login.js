import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Gamepad2, Eye, EyeOff } from 'lucide-react';

export default function Login() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (user) { navigate('/'); return null; }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : (Array.isArray(detail) ? detail.map(e => e.msg).join(' ') : 'Login failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-base flex items-center justify-center p-4">
      <div className="w-full max-w-md animate-fade-in">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Gamepad2 className="w-10 h-10 text-accent" />
            <h1 className="font-heading font-bold text-3xl">
              <span className="text-accent">NEON</span><span className="text-white">BET</span>
            </h1>
          </div>
          <p className="text-text-secondary text-sm">Sign in to start playing</p>
        </div>

        <form onSubmit={handleSubmit} data-testid="login-form" className="bg-surface rounded-xl border border-white/5 p-6 space-y-4 shadow-lg">
          {error && <div data-testid="login-error" className="bg-danger/10 border border-danger/20 text-danger text-sm px-4 py-2 rounded-md">{error}</div>}

          <div>
            <label className="text-xs tracking-widest uppercase font-bold text-text-secondary mb-1 block">Email</label>
            <input data-testid="login-email" type="email" value={email} onChange={e => setEmail(e.target.value)}
              className="w-full bg-elevated border border-white/5 rounded-md px-4 py-2.5 text-white placeholder-muted focus:border-accent/30 transition-colors"
              placeholder="your@email.com" required />
          </div>

          <div>
            <label className="text-xs tracking-widest uppercase font-bold text-text-secondary mb-1 block">Password</label>
            <div className="relative">
              <input data-testid="login-password" type={showPw ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)}
                className="w-full bg-elevated border border-white/5 rounded-md px-4 py-2.5 text-white placeholder-muted focus:border-accent/30 transition-colors pr-10"
                placeholder="Enter password" required />
              <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-white">
                {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button data-testid="login-submit" type="submit" disabled={loading}
            className="w-full bg-accent text-black font-bold py-2.5 rounded-md hover:bg-accent-hover transition-colors shadow-[0_0_15px_rgba(0,231,1,0.3)] disabled:opacity-50">
            {loading ? 'Signing in...' : 'Sign In'}
          </button>

          <p className="text-center text-sm text-text-secondary">
            Don't have an account?{' '}
            <Link to="/register" data-testid="register-link" className="text-accent hover:text-accent-hover transition-colors">Sign up</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
