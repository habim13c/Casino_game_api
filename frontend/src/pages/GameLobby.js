import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { API, apiHeaders } from '../contexts/AuthContext';
import { Search, Sparkles, Dice1, CreditCard, Target, Flame, Star, Clover, CircleDot } from 'lucide-react';

const GAME_ICONS = {
  slots: Sparkles, blackjack: CreditCard, roulette: CircleDot, crash: Flame,
  mines: Target, poker: Star, craps: Dice1, sicbo: Dice1,
  baccarat: CreditCard, wheel: CircleDot, dragon_tiger: Clover,
  video_poker: Star, hilo: Target, plinko: CircleDot,
  lottery: Sparkles, teen_patti: CreditCard, andar_bahar: Clover, keno: Target,
};

const GAME_COLORS = {
  slots: 'from-purple-500/20 to-pink-500/20', blackjack: 'from-green-500/20 to-emerald-500/20',
  roulette: 'from-red-500/20 to-orange-500/20', crash: 'from-amber-500/20 to-red-500/20',
  mines: 'from-blue-500/20 to-cyan-500/20', poker: 'from-indigo-500/20 to-purple-500/20',
  craps: 'from-yellow-500/20 to-amber-500/20', sicbo: 'from-teal-500/20 to-green-500/20',
  baccarat: 'from-rose-500/20 to-pink-500/20', wheel: 'from-violet-500/20 to-fuchsia-500/20',
  dragon_tiger: 'from-orange-500/20 to-red-500/20', video_poker: 'from-cyan-500/20 to-blue-500/20',
  hilo: 'from-lime-500/20 to-green-500/20', plinko: 'from-sky-500/20 to-indigo-500/20',
  lottery: 'from-fuchsia-500/20 to-pink-500/20', teen_patti: 'from-emerald-500/20 to-teal-500/20',
  andar_bahar: 'from-amber-500/20 to-orange-500/20', keno: 'from-pink-500/20 to-rose-500/20',
};

const CATEGORIES = ['all', 'cards', 'table', 'dice', 'instant', 'slots'];

export default function GameLobby() {
  const [games, setGames] = useState([]);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');

  useEffect(() => {
    axios.get(`${API}/api/games`, { headers: apiHeaders() }).then(r => setGames(r.data.games || [])).catch(() => {});
  }, []);

  const filtered = games.filter(g => {
    if (search) {
      const s = search.toLowerCase();
      const nameMatch = (g.name || '').toLowerCase().includes(s);
      const idMatch = (g.game_id || '').toLowerCase().includes(s);
      const catMatch = (g.category || '').toLowerCase().includes(s);
      if (!nameMatch && !idMatch && !catMatch) return false;
    }
    if (category !== 'all' && g.category !== category) return false;
    return g.enabled !== false;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 data-testid="lobby-title" className="font-heading text-3xl sm:text-4xl font-bold mb-2">
          Game <span className="text-accent">Lobby</span>
        </h1>
        <p className="text-text-secondary">Choose your game and start winning</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-4 mb-8">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
          <input data-testid="game-search" type="text" value={search} onChange={e => setSearch(e.target.value)}
            className="w-full bg-surface border border-white/5 rounded-md pl-10 pr-4 py-2.5 text-white placeholder-muted focus:border-accent/30 transition-colors"
            placeholder="Search games..." />
        </div>
        <div className="flex gap-1 overflow-x-auto pb-1">
          {CATEGORIES.map(cat => (
            <button key={cat} data-testid={`filter-${cat}`} onClick={() => setCategory(cat)}
              className={`px-4 py-2 text-sm rounded-md whitespace-nowrap transition-all ${
                category === cat ? 'bg-accent text-black font-bold' : 'bg-surface text-text-secondary hover:text-white hover:bg-elevated border border-white/5'
              }`}>
              {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
        {filtered.map((game, i) => {
          const Icon = GAME_ICONS[game.game_id] || Sparkles;
          const gradient = GAME_COLORS[game.game_id] || 'from-gray-500/20 to-gray-600/20';
          return (
            <Link key={game.game_id} to={`/game/${game.game_id}`} data-testid={`game-card-${game.game_id}`}
              className="group relative bg-surface border border-white/5 rounded-2xl overflow-hidden hover:-translate-y-1 hover:border-accent/30 hover:shadow-[0_4px_20px_rgba(0,231,1,0.1)] transition-all duration-300"
              style={{ animationDelay: `${i * 50}ms` }}>
              <div className={`aspect-square bg-gradient-to-br ${gradient} flex items-center justify-center relative`}>
                <Icon className="w-12 h-12 text-white/80 group-hover:text-accent transition-colors" />
                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-sm">
                  <span className="bg-accent text-black font-bold text-xs px-4 py-2 rounded-md shadow-[0_0_15px_rgba(0,231,1,0.3)]">
                    PLAY NOW
                  </span>
                </div>
              </div>
              <div className="p-3">
                <h3 className="font-heading text-sm font-semibold truncate">{game.name}</h3>
                <p className="text-xs text-text-secondary mt-0.5">${game.min_bet} - ${game.max_bet}</p>
              </div>
            </Link>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-20 text-text-secondary">
          <Sparkles className="w-12 h-12 mx-auto mb-4 text-muted" />
          <p className="text-lg">No games found</p>
        </div>
      )}
    </div>
  );
}
