import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { API, apiHeaders } from '../contexts/AuthContext';
import { Users, DollarSign, TrendingUp, Gamepad2, BarChart3, Settings, Shield, Search, ChevronDown } from 'lucide-react';

function StatCard({ icon: Icon, label, value, color = 'text-accent', sub }) {
  return (
    <div className="bg-surface rounded-xl border border-white/5 p-4">
      <div className="flex items-center gap-3 mb-2">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center bg-white/5`}>
          <Icon className={`w-4 h-4 ${color}`} />
        </div>
        <span className="text-xs text-text-secondary uppercase tracking-widest">{label}</span>
      </div>
      <p data-testid={`stat-${label.replace(/\s/g, '-').toLowerCase()}`} className={`font-heading text-xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-text-secondary mt-1">{sub}</p>}
    </div>
  );
}

export default function AdminDashboard() {
  const [tab, setTab] = useState('overview');
  const [dashboard, setDashboard] = useState(null);
  const [users, setUsers] = useState([]);
  const [userPage, setUserPage] = useState(1);
  const [userTotal, setUserTotal] = useState(0);
  const [userSearch, setUserSearch] = useState('');
  const [gameConfigs, setGameConfigs] = useState([]);
  const [bets, setBets] = useState([]);
  const [betPage, setBetPage] = useState(1);
  const [pnl, setPnl] = useState(null);
  const [audit, setAudit] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [adjustAmount, setAdjustAmount] = useState('');
  const [adjustReason, setAdjustReason] = useState('');

  const loadDashboard = useCallback(async () => {
    try { const { data } = await axios.get(`${API}/api/admin/dashboard`, { headers: apiHeaders() }); setDashboard(data); } catch {}
  }, []);

  const loadUsers = useCallback(async (p = 1) => {
    try {
      const { data } = await axios.get(`${API}/api/admin/users?page=${p}&limit=15&search=${userSearch}`, { headers: apiHeaders() });
      setUsers(data.users || []); setUserPage(p); setUserTotal(data.total || 0);
    } catch {}
  }, [userSearch]);

  const loadGameConfigs = useCallback(async () => {
    try { const { data } = await axios.get(`${API}/api/admin/games/config`, { headers: apiHeaders() }); setGameConfigs(data.configs || []); } catch {}
  }, []);

  const loadBets = useCallback(async (p = 1) => {
    try { const { data } = await axios.get(`${API}/api/admin/bets?page=${p}&limit=20`, { headers: apiHeaders() }); setBets(data.bets || []); setBetPage(p); } catch {}
  }, []);

  const loadPnl = useCallback(async () => {
    try { const { data } = await axios.get(`${API}/api/admin/reports/pnl?days=30`, { headers: apiHeaders() }); setPnl(data); } catch {}
  }, []);

  const loadAudit = useCallback(async () => {
    try { const { data } = await axios.get(`${API}/api/admin/audit`, { headers: apiHeaders() }); setAudit(data.actions || []); } catch {}
  }, []);

  useEffect(() => { loadDashboard(); }, [loadDashboard]);
  useEffect(() => {
    if (tab === 'users') loadUsers();
    if (tab === 'games') loadGameConfigs();
    if (tab === 'bets') loadBets();
    if (tab === 'reports') loadPnl();
    if (tab === 'audit') loadAudit();
  }, [tab, loadUsers, loadGameConfigs, loadBets, loadPnl, loadAudit]);

  const handleToggleGame = async (gameId, enabled) => {
    try {
      await axios.patch(`${API}/api/admin/games/${gameId}/config`, { enabled: !enabled }, { headers: apiHeaders() });
      loadGameConfigs();
    } catch {}
  };

  const handleAdjustBalance = async (userId) => {
    const amt = parseFloat(adjustAmount);
    if (!amt || !adjustReason) return;
    try {
      await axios.patch(`${API}/api/admin/users/${userId}/balance`, { amount: amt, reason: adjustReason }, { headers: apiHeaders() });
      setAdjustAmount(''); setAdjustReason(''); setSelectedUser(null); loadUsers();
    } catch {}
  };

  const handleStatusChange = async (userId, status) => {
    try {
      await axios.patch(`${API}/api/admin/users/${userId}/status`, { status, reason: 'Admin action' }, { headers: apiHeaders() });
      loadUsers();
    } catch {}
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'games', label: 'Games', icon: Gamepad2 },
    { id: 'bets', label: 'Bets', icon: DollarSign },
    { id: 'reports', label: 'P&L', icon: TrendingUp },
    { id: 'audit', label: 'Audit', icon: Shield },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 data-testid="admin-title" className="font-heading text-3xl font-bold mb-6">
        Admin <span className="text-gold">Panel</span>
      </h1>

      <div className="flex gap-1 mb-6 overflow-x-auto pb-1">
        {tabs.map(t => (
          <button key={t.id} data-testid={`admin-tab-${t.id}`} onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-4 py-2 text-sm rounded-md whitespace-nowrap transition-all ${
              tab === t.id ? 'bg-gold/10 text-gold border border-gold/20' : 'text-text-secondary hover:text-white hover:bg-white/5'
            }`}>
            <t.icon className="w-4 h-4" /> {t.label}
          </button>
        ))}
      </div>

      {tab === 'overview' && dashboard && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard icon={Users} label="Total Users" value={dashboard.total_users} />
          <StatCard icon={Users} label="Active Users" value={dashboard.active_users} color="text-accent" />
          <StatCard icon={Gamepad2} label="Total Bets" value={dashboard.total_bets} color="text-gold" />
          <StatCard icon={Gamepad2} label="Bets Today" value={dashboard.bets_today} color="text-gold" />
          <StatCard icon={DollarSign} label="Total Wagered" value={`$${dashboard.total_wagered}`} color="text-white" />
          <StatCard icon={DollarSign} label="Total Paid" value={`$${dashboard.total_paid}`} color="text-danger" />
          <StatCard icon={TrendingUp} label="GGR" value={`$${dashboard.ggr}`} color={dashboard.ggr >= 0 ? 'text-accent' : 'text-danger'} />
          <StatCard icon={TrendingUp} label="GGR Today" value={`$${dashboard.today_ggr}`} color={dashboard.today_ggr >= 0 ? 'text-accent' : 'text-danger'} />
        </div>
      )}

      {tab === 'users' && (
        <div className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
            <input data-testid="admin-user-search" value={userSearch} onChange={e => setUserSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && loadUsers()}
              className="w-full bg-surface border border-white/5 rounded-md pl-10 pr-4 py-2.5 text-white placeholder-muted" placeholder="Search users..." />
          </div>
          <div className="bg-surface rounded-xl border border-white/5 overflow-hidden">
            <table className="w-full">
              <thead><tr className="border-b border-white/5">
                <th className="text-left text-xs text-text-secondary uppercase px-4 py-3">User</th>
                <th className="text-right text-xs text-text-secondary uppercase px-4 py-3">Balance</th>
                <th className="text-center text-xs text-text-secondary uppercase px-4 py-3">Role</th>
                <th className="text-center text-xs text-text-secondary uppercase px-4 py-3">Status</th>
                <th className="text-right text-xs text-text-secondary uppercase px-4 py-3">Actions</th>
              </tr></thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id} data-testid={`admin-user-row-${u.id}`} className="border-b border-white/5 hover:bg-white/[0.02]">
                    <td className="px-4 py-3"><p className="text-sm font-medium">{u.name || u.email}</p><p className="text-xs text-text-secondary">{u.email}</p></td>
                    <td className="px-4 py-3 text-right text-sm text-accent font-semibold">${u.balance?.toFixed(2)}</td>
                    <td className="px-4 py-3 text-center"><span className={`text-xs px-2 py-0.5 rounded-full ${u.role === 'super_admin' ? 'bg-gold/10 text-gold' : u.role === 'admin' ? 'bg-accent/10 text-accent' : 'bg-white/5 text-text-secondary'}`}>{u.role}</span></td>
                    <td className="px-4 py-3 text-center"><span className={`text-xs px-2 py-0.5 rounded-full ${u.status === 'active' ? 'bg-accent/10 text-accent' : u.status === 'frozen' ? 'bg-gold/10 text-gold' : 'bg-danger/10 text-danger'}`}>{u.status}</span></td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex gap-1 justify-end">
                        <button onClick={() => setSelectedUser(selectedUser === u.id ? null : u.id)} className="text-xs px-2 py-1 bg-elevated rounded hover:bg-white/10 text-text-secondary">
                          <Settings className="w-3 h-3 inline" />
                        </button>
                        {u.status === 'active' ? (
                          <button data-testid={`freeze-user-${u.id}`} onClick={() => handleStatusChange(u.id, 'frozen')} className="text-xs px-2 py-1 bg-gold/10 text-gold rounded hover:bg-gold/20">Freeze</button>
                        ) : (
                          <button data-testid={`activate-user-${u.id}`} onClick={() => handleStatusChange(u.id, 'active')} className="text-xs px-2 py-1 bg-accent/10 text-accent rounded hover:bg-accent/20">Activate</button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {selectedUser && (
            <div className="bg-surface rounded-xl border border-gold/20 p-4">
              <h3 className="font-heading text-sm font-semibold mb-3 text-gold">Adjust Balance</h3>
              <div className="flex gap-2">
                <input data-testid="admin-adjust-amount" type="number" value={adjustAmount} onChange={e => setAdjustAmount(e.target.value)}
                  className="flex-1 bg-elevated border border-white/5 rounded-md px-3 py-2 text-white text-sm" placeholder="Amount (+/-)" />
                <input data-testid="admin-adjust-reason" type="text" value={adjustReason} onChange={e => setAdjustReason(e.target.value)}
                  className="flex-1 bg-elevated border border-white/5 rounded-md px-3 py-2 text-white text-sm" placeholder="Reason" />
                <button data-testid="admin-adjust-submit" onClick={() => handleAdjustBalance(selectedUser)}
                  className="bg-gold text-black font-bold px-4 py-2 rounded-md text-sm">Apply</button>
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'games' && (
        <div className="bg-surface rounded-xl border border-white/5 overflow-hidden">
          <table className="w-full">
            <thead><tr className="border-b border-white/5">
              <th className="text-left text-xs text-text-secondary uppercase px-4 py-3">Game</th>
              <th className="text-center text-xs text-text-secondary uppercase px-4 py-3">Category</th>
              <th className="text-right text-xs text-text-secondary uppercase px-4 py-3">House Edge</th>
              <th className="text-right text-xs text-text-secondary uppercase px-4 py-3">Min/Max Bet</th>
              <th className="text-center text-xs text-text-secondary uppercase px-4 py-3">Status</th>
            </tr></thead>
            <tbody>
              {gameConfigs.map(g => (
                <tr key={g.game_id} data-testid={`admin-game-${g.game_id}`} className="border-b border-white/5 hover:bg-white/[0.02]">
                  <td className="px-4 py-3 text-sm font-medium">{g.name}</td>
                  <td className="px-4 py-3 text-center text-xs text-text-secondary capitalize">{g.category}</td>
                  <td className="px-4 py-3 text-right text-sm">{g.house_edge}%</td>
                  <td className="px-4 py-3 text-right text-sm text-text-secondary">${g.min_bet} - ${g.max_bet}</td>
                  <td className="px-4 py-3 text-center">
                    <button data-testid={`toggle-game-${g.game_id}`} onClick={() => handleToggleGame(g.game_id, g.enabled)}
                      className={`text-xs px-3 py-1 rounded-full transition-colors ${g.enabled ? 'bg-accent/10 text-accent hover:bg-accent/20' : 'bg-danger/10 text-danger hover:bg-danger/20'}`}>
                      {g.enabled ? 'Enabled' : 'Disabled'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'bets' && (
        <div className="bg-surface rounded-xl border border-white/5 overflow-hidden">
          <table className="w-full">
            <thead><tr className="border-b border-white/5">
              <th className="text-left text-xs text-text-secondary uppercase px-4 py-3">User</th>
              <th className="text-left text-xs text-text-secondary uppercase px-4 py-3">Game</th>
              <th className="text-right text-xs text-text-secondary uppercase px-4 py-3">Bet</th>
              <th className="text-right text-xs text-text-secondary uppercase px-4 py-3">Won</th>
              <th className="text-right text-xs text-text-secondary uppercase px-4 py-3">Multi</th>
              <th className="text-right text-xs text-text-secondary uppercase px-4 py-3">Date</th>
            </tr></thead>
            <tbody>
              {bets.map((b, i) => (
                <tr key={i} data-testid={`admin-bet-${i}`} className="border-b border-white/5 hover:bg-white/[0.02]">
                  <td className="px-4 py-3 text-sm text-text-secondary">{b.user_id?.slice(-6)}</td>
                  <td className="px-4 py-3 text-sm capitalize">{b.game?.replace(/_/g, ' ')}</td>
                  <td className="px-4 py-3 text-sm text-right">${b.bet_amount?.toFixed(2)}</td>
                  <td className="px-4 py-3 text-sm text-right">${b.win_amount?.toFixed(2)}</td>
                  <td className="px-4 py-3 text-sm text-right">{b.multiplier}x</td>
                  <td className="px-4 py-3 text-sm text-right text-text-secondary">{new Date(b.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {bets.length === 0 && <div className="py-12 text-center text-text-secondary text-sm">No bets yet</div>}
        </div>
      )}

      {tab === 'reports' && pnl && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard icon={DollarSign} label="Total Wagered" value={`$${pnl.total_wagered}`} />
            <StatCard icon={DollarSign} label="Total Paid" value={`$${pnl.total_paid}`} color="text-danger" />
            <StatCard icon={TrendingUp} label="GGR" value={`$${pnl.ggr}`} color={pnl.ggr >= 0 ? 'text-accent' : 'text-danger'} />
            <StatCard icon={TrendingUp} label="Hold %" value={`${pnl.hold_pct}%`} color="text-gold" />
          </div>
          <div className="bg-surface rounded-xl border border-white/5 overflow-hidden">
            <table className="w-full">
              <thead><tr className="border-b border-white/5">
                <th className="text-left text-xs text-text-secondary uppercase px-4 py-3">Game</th>
                <th className="text-right text-xs text-text-secondary uppercase px-4 py-3">Bets</th>
                <th className="text-right text-xs text-text-secondary uppercase px-4 py-3">Wagered</th>
                <th className="text-right text-xs text-text-secondary uppercase px-4 py-3">Paid</th>
                <th className="text-right text-xs text-text-secondary uppercase px-4 py-3">GGR</th>
              </tr></thead>
              <tbody>
                {(pnl.by_game || []).map(g => (
                  <tr key={g.game} className="border-b border-white/5">
                    <td className="px-4 py-3 text-sm capitalize">{g.game?.replace(/_/g, ' ')}</td>
                    <td className="px-4 py-3 text-sm text-right">{g.bets}</td>
                    <td className="px-4 py-3 text-sm text-right">${g.wagered}</td>
                    <td className="px-4 py-3 text-sm text-right">${g.paid}</td>
                    <td className={`px-4 py-3 text-sm text-right font-semibold ${g.ggr >= 0 ? 'text-accent' : 'text-danger'}`}>${g.ggr}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'audit' && (
        <div className="bg-surface rounded-xl border border-white/5 overflow-hidden">
          <table className="w-full">
            <thead><tr className="border-b border-white/5">
              <th className="text-left text-xs text-text-secondary uppercase px-4 py-3">Action</th>
              <th className="text-left text-xs text-text-secondary uppercase px-4 py-3">Target</th>
              <th className="text-left text-xs text-text-secondary uppercase px-4 py-3">Reason</th>
              <th className="text-right text-xs text-text-secondary uppercase px-4 py-3">Time</th>
            </tr></thead>
            <tbody>
              {audit.map((a, i) => (
                <tr key={i} className="border-b border-white/5">
                  <td className="px-4 py-3 text-sm">{a.action_type}</td>
                  <td className="px-4 py-3 text-sm text-text-secondary">{a.target_type}: {a.target_id?.slice(-6)}</td>
                  <td className="px-4 py-3 text-sm text-text-secondary">{a.reason}</td>
                  <td className="px-4 py-3 text-sm text-right text-text-secondary">{new Date(a.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {audit.length === 0 && <div className="py-12 text-center text-text-secondary text-sm">No audit log entries</div>}
        </div>
      )}
    </div>
  );
}
