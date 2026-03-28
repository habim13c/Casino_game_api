import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Wallet, History, User, LogOut, Shield, Menu, X, Gamepad2 } from 'lucide-react';

export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const isAdmin = user && ['admin', 'super_admin'].includes(user.role);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header data-testid="main-header" className="sticky top-0 z-50 backdrop-blur-xl bg-base/60 border-b border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2 group" data-testid="logo-link">
            <Gamepad2 className="w-7 h-7 text-accent group-hover:text-accent-hover transition-colors" />
            <span className="font-heading font-bold text-lg tracking-tight">
              <span className="text-accent">NEON</span><span className="text-white">BET</span>
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-1">
            <Link to="/" data-testid="nav-games" className="px-3 py-2 text-sm text-text-secondary hover:text-white transition-colors rounded-md hover:bg-white/5">
              <Gamepad2 className="w-4 h-4 inline mr-1" /> Games
            </Link>
            <Link to="/wallet" data-testid="nav-wallet" className="px-3 py-2 text-sm text-text-secondary hover:text-white transition-colors rounded-md hover:bg-white/5">
              <Wallet className="w-4 h-4 inline mr-1" /> Wallet
            </Link>
            <Link to="/history" data-testid="nav-history" className="px-3 py-2 text-sm text-text-secondary hover:text-white transition-colors rounded-md hover:bg-white/5">
              <History className="w-4 h-4 inline mr-1" /> History
            </Link>
            <Link to="/profile" data-testid="nav-profile" className="px-3 py-2 text-sm text-text-secondary hover:text-white transition-colors rounded-md hover:bg-white/5">
              <User className="w-4 h-4 inline mr-1" /> Profile
            </Link>
            {isAdmin && (
              <Link to="/admin" data-testid="nav-admin" className="px-3 py-2 text-sm text-gold hover:text-accent transition-colors rounded-md hover:bg-white/5">
                <Shield className="w-4 h-4 inline mr-1" /> Admin
              </Link>
            )}
          </div>

          <div className="hidden md:flex items-center gap-3">
            {user && (
              <div data-testid="balance-display" className="flex items-center gap-2 bg-elevated px-3 py-1.5 rounded-md border border-white/5">
                <span className="text-xs text-text-secondary">BAL</span>
                <span className="text-sm font-semibold text-accent">${(user.balance || 0).toFixed(2)}</span>
              </div>
            )}
            <button data-testid="logout-btn" onClick={handleLogout} className="p-2 text-text-secondary hover:text-danger transition-colors rounded-md hover:bg-white/5">
              <LogOut className="w-4 h-4" />
            </button>
          </div>

          <button className="md:hidden p-2" onClick={() => setMenuOpen(!menuOpen)}>
            {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {menuOpen && (
        <div className="md:hidden bg-surface border-t border-white/5 py-3 px-4 space-y-2">
          <div className="flex items-center gap-2 bg-elevated px-3 py-2 rounded-md border border-white/5 mb-3">
            <span className="text-xs text-text-secondary">BAL</span>
            <span className="text-sm font-semibold text-accent">${(user?.balance || 0).toFixed(2)}</span>
          </div>
          <Link to="/" onClick={() => setMenuOpen(false)} className="block px-3 py-2 text-sm text-text-secondary hover:text-white rounded-md hover:bg-white/5">Games</Link>
          <Link to="/wallet" onClick={() => setMenuOpen(false)} className="block px-3 py-2 text-sm text-text-secondary hover:text-white rounded-md hover:bg-white/5">Wallet</Link>
          <Link to="/history" onClick={() => setMenuOpen(false)} className="block px-3 py-2 text-sm text-text-secondary hover:text-white rounded-md hover:bg-white/5">History</Link>
          <Link to="/profile" onClick={() => setMenuOpen(false)} className="block px-3 py-2 text-sm text-text-secondary hover:text-white rounded-md hover:bg-white/5">Profile</Link>
          {isAdmin && <Link to="/admin" onClick={() => setMenuOpen(false)} className="block px-3 py-2 text-sm text-gold rounded-md hover:bg-white/5">Admin</Link>}
          <button onClick={handleLogout} className="w-full text-left px-3 py-2 text-sm text-danger rounded-md hover:bg-white/5">Logout</button>
        </div>
      )}
    </header>
  );
}
