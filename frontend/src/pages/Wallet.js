import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API, apiHeaders, useAuth } from '../contexts/AuthContext';
import { ArrowUpRight, ArrowDownRight, DollarSign, CreditCard } from 'lucide-react';

export default function Wallet() {
  const { refreshUser, user } = useAuth();
  const [amount, setAmount] = useState('');
  const [txns, setTxns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const loadTxns = async (p = 1) => {
    try {
      const { data } = await axios.get(`${API}/api/user/transactions?page=${p}&limit=15`, { headers: apiHeaders() });
      setTxns(data.transactions || []);
      setTotalPages(data.pages || 1);
      setPage(p);
    } catch {}
  };

  useEffect(() => { loadTxns(); }, []);

  const handleAction = async (action) => {
    const amt = parseFloat(amount);
    if (!amt || amt <= 0) { setError('Enter a valid amount'); return; }
    setLoading(true); setError(''); setSuccess('');
    try {
      const { data } = await axios.post(`${API}/api/user/${action}`, { amount: amt }, { headers: apiHeaders() });
      setSuccess(data.message);
      setAmount('');
      refreshUser();
      loadTxns();
    } catch (err) {
      setError(err.response?.data?.detail || 'Transaction failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 data-testid="wallet-title" className="font-heading text-3xl font-bold mb-8">
        <span className="text-accent">Wallet</span>
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-surface rounded-xl border border-white/5 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center">
              <DollarSign className="w-5 h-5 text-accent" />
            </div>
            <div>
              <p className="text-xs text-text-secondary uppercase tracking-widest">Main Balance</p>
              <p data-testid="main-balance" className="font-heading text-2xl font-bold text-accent">${(user?.balance || 0).toFixed(2)}</p>
            </div>
          </div>
        </div>

        <div className="bg-surface rounded-xl border border-white/5 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-gold/10 rounded-lg flex items-center justify-center">
              <CreditCard className="w-5 h-5 text-gold" />
            </div>
            <div>
              <p className="text-xs text-text-secondary uppercase tracking-widest">Bonus Balance</p>
              <p data-testid="bonus-balance" className="font-heading text-2xl font-bold text-gold">${(user?.bonus_balance || 0).toFixed(2)}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-surface rounded-xl border border-white/5 p-6 mb-8">
        <h2 className="font-heading text-lg font-semibold mb-4">Quick Actions</h2>
        {error && <div data-testid="wallet-error" className="bg-danger/10 border border-danger/20 text-danger text-sm px-4 py-2 rounded-md mb-4">{error}</div>}
        {success && <div data-testid="wallet-success" className="bg-accent/10 border border-accent/20 text-accent text-sm px-4 py-2 rounded-md mb-4">{success}</div>}
        <div className="flex gap-3">
          <input data-testid="wallet-amount" type="number" value={amount} onChange={e => setAmount(e.target.value)}
            className="flex-1 bg-elevated border border-white/5 rounded-md px-4 py-2.5 text-white placeholder-muted focus:border-accent/30 transition-colors"
            placeholder="Enter amount" min="1" />
          <button data-testid="deposit-btn" onClick={() => handleAction('deposit')} disabled={loading}
            className="bg-accent text-black font-bold px-6 py-2.5 rounded-md hover:bg-accent-hover transition-colors disabled:opacity-50">
            Deposit
          </button>
          <button data-testid="withdraw-btn" onClick={() => handleAction('withdraw')} disabled={loading}
            className="bg-elevated border border-white/10 text-white font-bold px-6 py-2.5 rounded-md hover:bg-white/10 transition-colors disabled:opacity-50">
            Withdraw
          </button>
        </div>
      </div>

      <div className="bg-surface rounded-xl border border-white/5 p-6">
        <h2 className="font-heading text-lg font-semibold mb-4">Transaction History</h2>
        <div className="space-y-2">
          {txns.length === 0 ? (
            <p className="text-text-secondary text-sm py-8 text-center">No transactions yet</p>
          ) : txns.map((tx, i) => (
            <div key={i} data-testid={`txn-${i}`} className="flex items-center justify-between p-3 bg-base rounded-lg">
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${tx.amount >= 0 ? 'bg-accent/10' : 'bg-danger/10'}`}>
                  {tx.amount >= 0 ? <ArrowUpRight className="w-4 h-4 text-accent" /> : <ArrowDownRight className="w-4 h-4 text-danger" />}
                </div>
                <div>
                  <p className="text-sm font-medium">{tx.description}</p>
                  <p className="text-xs text-text-secondary">{tx.type} - {new Date(tx.created_at).toLocaleDateString()}</p>
                </div>
              </div>
              <div className="text-right">
                <p className={`font-semibold text-sm ${tx.amount >= 0 ? 'text-accent' : 'text-danger'}`}>
                  {tx.amount >= 0 ? '+' : ''}{tx.amount?.toFixed(2)}
                </p>
                <p className="text-xs text-text-secondary">${tx.balance_after?.toFixed(2)}</p>
              </div>
            </div>
          ))}
        </div>
        {totalPages > 1 && (
          <div className="flex justify-center gap-2 mt-4">
            <button disabled={page <= 1} onClick={() => loadTxns(page - 1)}
              className="px-3 py-1 bg-elevated rounded text-sm text-text-secondary disabled:opacity-30">Prev</button>
            <span className="px-3 py-1 text-sm text-text-secondary">{page} / {totalPages}</span>
            <button disabled={page >= totalPages} onClick={() => loadTxns(page + 1)}
              className="px-3 py-1 bg-elevated rounded text-sm text-text-secondary disabled:opacity-30">Next</button>
          </div>
        )}
      </div>
    </div>
  );
}
