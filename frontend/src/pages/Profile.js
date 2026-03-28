import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API, apiHeaders, useAuth } from '../contexts/AuthContext';
import { User, Trophy, TrendingUp, Star } from 'lucide-react';

export default function Profile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    axios.get(`${API}/api/user/profile`, { headers: apiHeaders() }).then(r => setProfile(r.data)).catch(() => {});
  }, []);

  if (!profile) return <div className="min-h-screen flex items-center justify-center"><div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" /></div>;

  const stats = profile.stats || {};

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 data-testid="profile-title" className="font-heading text-3xl font-bold mb-8">
        <span className="text-accent">Profile</span>
      </h1>

      <div className="bg-surface rounded-xl border border-white/5 p-6 mb-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 bg-accent/10 rounded-full flex items-center justify-center">
            <User className="w-8 h-8 text-accent" />
          </div>
          <div>
            <h2 data-testid="profile-name" className="font-heading text-xl font-bold">{profile.display_name || profile.name}</h2>
            <p className="text-text-secondary text-sm">{profile.email}</p>
            <span className="inline-block mt-1 text-xs px-2 py-0.5 bg-accent/10 text-accent rounded-full">{profile.role}</span>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-base p-4 rounded-lg">
            <p className="text-xs text-text-secondary uppercase tracking-widest mb-1">VIP Tier</p>
            <p className="font-heading text-lg font-bold flex items-center gap-1"><Star className="w-4 h-4 text-gold" /> {profile.vip_tier}</p>
          </div>
          <div className="bg-base p-4 rounded-lg">
            <p className="text-xs text-text-secondary uppercase tracking-widest mb-1">Loyalty Points</p>
            <p className="font-heading text-lg font-bold text-gold">{profile.loyalty_points}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-surface rounded-xl border border-white/5 p-4">
          <Trophy className="w-5 h-5 text-accent mb-2" />
          <p className="text-xs text-text-secondary">Total Bets</p>
          <p data-testid="total-bets" className="font-heading text-lg font-bold">{stats.total_bets || 0}</p>
        </div>
        <div className="bg-surface rounded-xl border border-white/5 p-4">
          <TrendingUp className="w-5 h-5 text-gold mb-2" />
          <p className="text-xs text-text-secondary">Wagered</p>
          <p data-testid="total-wagered" className="font-heading text-lg font-bold">${stats.total_wagered || 0}</p>
        </div>
        <div className="bg-surface rounded-xl border border-white/5 p-4">
          <Trophy className="w-5 h-5 text-accent mb-2" />
          <p className="text-xs text-text-secondary">Total Won</p>
          <p className="font-heading text-lg font-bold text-accent">${stats.total_won || 0}</p>
        </div>
        <div className="bg-surface rounded-xl border border-white/5 p-4">
          <TrendingUp className="w-5 h-5 mb-2" style={{ color: (stats.net_profit || 0) >= 0 ? '#00E701' : '#FF2A55' }} />
          <p className="text-xs text-text-secondary">Net Profit</p>
          <p className={`font-heading text-lg font-bold ${(stats.net_profit || 0) >= 0 ? 'text-accent' : 'text-danger'}`}>${stats.net_profit || 0}</p>
        </div>
      </div>
    </div>
  );
}
