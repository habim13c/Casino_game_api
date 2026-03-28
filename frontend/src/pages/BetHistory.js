import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API, apiHeaders } from '../contexts/AuthContext';
import { Filter } from 'lucide-react';

export default function BetHistory() {
  const [bets, setBets] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [gameFilter, setGameFilter] = useState('');

  const loadBets = async (p = 1) => {
    try {
      const url = `${API}/api/user/bets?page=${p}&limit=20${gameFilter ? `&game=${gameFilter}` : ''}`;
      const { data } = await axios.get(url, { headers: apiHeaders() });
      setBets(data.bets || []);
      setTotalPages(data.pages || 1);
      setPage(p);
    } catch {}
  };

  useEffect(() => { loadBets(); }, [gameFilter]);

  const GAMES = ['', 'slots', 'blackjack', 'roulette', 'crash', 'mines', 'poker', 'craps', 'sicbo', 'baccarat', 'wheel', 'dragon_tiger', 'video_poker', 'hilo', 'plinko', 'lottery', 'teen_patti', 'andar_bahar', 'keno'];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 data-testid="history-title" className="font-heading text-3xl font-bold">
          Bet <span className="text-accent">History</span>
        </h1>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-text-secondary" />
          <select data-testid="game-filter" value={gameFilter} onChange={e => setGameFilter(e.target.value)}
            className="bg-surface border border-white/5 rounded-md px-3 py-1.5 text-sm text-white focus:border-accent/30">
            <option value="">All Games</option>
            {GAMES.filter(Boolean).map(g => <option key={g} value={g}>{g.replace(/_/g, ' ')}</option>)}
          </select>
        </div>
      </div>

      <div className="bg-surface rounded-xl border border-white/5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                <th className="text-left text-xs text-text-secondary uppercase tracking-wider px-4 py-3">Game</th>
                <th className="text-right text-xs text-text-secondary uppercase tracking-wider px-4 py-3">Bet</th>
                <th className="text-right text-xs text-text-secondary uppercase tracking-wider px-4 py-3">Won</th>
                <th className="text-right text-xs text-text-secondary uppercase tracking-wider px-4 py-3">Multi</th>
                <th className="text-right text-xs text-text-secondary uppercase tracking-wider px-4 py-3">Profit</th>
                <th className="text-right text-xs text-text-secondary uppercase tracking-wider px-4 py-3">Date</th>
              </tr>
            </thead>
            <tbody>
              {bets.map((bet, i) => {
                const profit = bet.win_amount - bet.bet_amount;
                return (
                  <tr key={i} data-testid={`bet-row-${i}`} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3 text-sm font-medium capitalize">{bet.game?.replace(/_/g, ' ')}</td>
                    <td className="px-4 py-3 text-sm text-right">${bet.bet_amount?.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm text-right">${bet.win_amount?.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm text-right">{bet.multiplier}x</td>
                    <td className={`px-4 py-3 text-sm text-right font-semibold ${profit >= 0 ? 'text-accent' : 'text-danger'}`}>
                      {profit >= 0 ? '+' : ''}{profit.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-text-secondary">{new Date(bet.created_at).toLocaleDateString()}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {bets.length === 0 && <div className="py-12 text-center text-text-secondary text-sm">No bets found</div>}
      </div>

      {totalPages > 1 && (
        <div className="flex justify-center gap-2 mt-4">
          <button disabled={page <= 1} onClick={() => loadBets(page - 1)}
            className="px-4 py-2 bg-surface border border-white/5 rounded-md text-sm text-text-secondary disabled:opacity-30 hover:bg-elevated">Prev</button>
          <span className="px-4 py-2 text-sm text-text-secondary">{page} / {totalPages}</span>
          <button disabled={page >= totalPages} onClick={() => loadBets(page + 1)}
            className="px-4 py-2 bg-surface border border-white/5 rounded-md text-sm text-text-secondary disabled:opacity-30 hover:bg-elevated">Next</button>
        </div>
      )}
    </div>
  );
}
