import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { API, apiHeaders, useAuth } from '../contexts/AuthContext';
import { ArrowLeft, Zap, Trophy, TrendingUp } from 'lucide-react';

const GAME_PARAMS = {
  roulette: [
    { key: 'bet_type', label: 'Bet Type', type: 'select', options: ['color', 'parity', 'dozen', 'half', 'straight'], default: 'color' },
    { key: 'value', label: 'Value', type: 'dynamic' },
  ],
  crash: [{ key: 'auto_cashout', label: 'Auto Cashout', type: 'number', default: 2.0, min: 1.01, step: 0.1 }],
  mines: [
    { key: 'mines_count', label: 'Mines', type: 'number', default: 3, min: 1, max: 24 },
    { key: 'tiles_revealed', label: 'Tiles to Reveal', type: 'number', default: 5, min: 1, max: 24 },
  ],
  craps: [{ key: 'bet_type', label: 'Bet Type', type: 'select', options: ['pass', 'dont_pass', 'field', 'any_seven'], default: 'pass' }],
  sicbo: [
    { key: 'bet_type', label: 'Bet Type', type: 'select', options: ['big', 'small', 'triple', 'total'], default: 'big' },
  ],
  baccarat: [{ key: 'bet_on', label: 'Bet On', type: 'select', options: ['player', 'banker', 'tie'], default: 'player' }],
  dragon_tiger: [{ key: 'bet_on', label: 'Bet On', type: 'select', options: ['dragon', 'tiger', 'tie'], default: 'dragon' }],
  hilo: [{ key: 'guess', label: 'Guess', type: 'select', options: ['higher', 'lower'], default: 'higher' }],
  plinko: [{ key: 'risk', label: 'Risk', type: 'select', options: ['low', 'medium', 'high'], default: 'medium' }],
  teen_patti: [{ key: 'bet_on', label: 'Bet On', type: 'select', options: ['player', 'dealer', 'tie'], default: 'player' }],
  andar_bahar: [{ key: 'bet_on', label: 'Bet On', type: 'select', options: ['andar', 'bahar'], default: 'andar' }],
  lottery: [],
  keno: [],
};

const ROULETTE_VALUES = {
  color: ['red', 'black'], parity: ['even', 'odd'], dozen: ['1st', '2nd', '3rd'], half: ['1-18', '19-36'], straight: Array.from({ length: 37 }, (_, i) => String(i)),
};

export default function GamePlay() {
  const { gameId } = useParams();
  const { refreshUser } = useAuth();
  const [gameInfo, setGameInfo] = useState(null);
  const [betAmount, setBetAmount] = useState(10);
  const [params, setParams] = useState({});
  const [result, setResult] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);

  useEffect(() => {
    axios.get(`${API}/api/games/${gameId}`, { headers: apiHeaders() }).then(r => {
      setGameInfo(r.data);
      setBetAmount(r.data.min_bet || 10);
    }).catch(() => {});
  }, [gameId]);

  const initParams = useCallback(() => {
    const gp = GAME_PARAMS[gameId] || [];
    const p = {};
    gp.forEach(param => {
      if (param.default !== undefined) p[param.key] = param.default;
    });
    setParams(p);
  }, [gameId]);

  useEffect(() => { initParams(); }, [initParams]);

  const play = async () => {
    setPlaying(true);
    setError('');
    setResult(null);
    try {
      const { data } = await axios.post(`${API}/api/games/${gameId}/play`, { bet_amount: betAmount, params }, { headers: apiHeaders() });
      setResult(data);
      setHistory(prev => [data, ...prev].slice(0, 10));
      refreshUser();
    } catch (err) {
      setError(err.response?.data?.detail || 'Game error');
    } finally {
      setPlaying(false);
    }
  };

  const renderResult = () => {
    if (!result) return null;
    const r = result.result || {};
    const isWin = result.win_amount > result.bet_amount;
    return (
      <div data-testid="game-result" className={`mt-4 p-4 rounded-xl border ${isWin ? 'bg-accent/5 border-accent/20' : 'bg-danger/5 border-danger/20'}`}>
        <div className="flex items-center gap-2 mb-3">
          {isWin ? <Trophy className="w-5 h-5 text-accent" /> : <Zap className="w-5 h-5 text-danger" />}
          <span className={`font-heading font-bold text-lg ${isWin ? 'text-accent' : 'text-danger'}`}>
            {isWin ? 'YOU WIN!' : 'Better luck next time'}
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
          <div><span className="text-text-secondary">Bet:</span> <span className="font-semibold">${result.bet_amount}</span></div>
          <div><span className="text-text-secondary">Won:</span> <span className={`font-semibold ${isWin ? 'text-accent' : 'text-danger'}`}>${result.win_amount}</span></div>
          <div><span className="text-text-secondary">Multi:</span> <span className="font-semibold">{result.multiplier}x</span></div>
          <div><span className="text-text-secondary">Balance:</span> <span className="font-semibold text-accent">${result.balance}</span></div>
        </div>
        <div className="mt-3 p-3 bg-base/50 rounded-lg text-xs text-text-secondary space-y-1">
          {Object.entries(r).filter(([k]) => !['is_win'].includes(k)).slice(0, 6).map(([key, val]) => (
            <div key={key}><span className="text-muted">{key.replace(/_/g, ' ')}:</span> {typeof val === 'object' ? JSON.stringify(val) : String(val)}</div>
          ))}
        </div>
      </div>
    );
  };

  const renderParams = () => {
    const gp = GAME_PARAMS[gameId] || [];
    return gp.map(param => {
      if (param.type === 'select') {
        return (
          <div key={param.key}>
            <label className="text-xs tracking-widest uppercase font-bold text-text-secondary mb-1 block">{param.label}</label>
            <select data-testid={`param-${param.key}`} value={params[param.key] || param.default}
              onChange={e => setParams(prev => ({ ...prev, [param.key]: e.target.value }))}
              className="w-full bg-elevated border border-white/5 rounded-md px-4 py-2.5 text-white focus:border-accent/30 transition-colors">
              {param.options.map(opt => <option key={opt} value={opt}>{opt}</option>)}
            </select>
          </div>
        );
      }
      if (param.type === 'dynamic' && gameId === 'roulette') {
        const bt = params.bet_type || 'color';
        const vals = ROULETTE_VALUES[bt] || [];
        return (
          <div key={param.key}>
            <label className="text-xs tracking-widest uppercase font-bold text-text-secondary mb-1 block">{param.label}</label>
            <select data-testid={`param-${param.key}`} value={params[param.key] || vals[0]}
              onChange={e => setParams(prev => ({ ...prev, [param.key]: e.target.value }))}
              className="w-full bg-elevated border border-white/5 rounded-md px-4 py-2.5 text-white focus:border-accent/30 transition-colors">
              {vals.map(v => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>
        );
      }
      if (param.type === 'number') {
        return (
          <div key={param.key}>
            <label className="text-xs tracking-widest uppercase font-bold text-text-secondary mb-1 block">{param.label}</label>
            <input data-testid={`param-${param.key}`} type="number" value={params[param.key] ?? param.default}
              min={param.min} max={param.max} step={param.step || 1}
              onChange={e => setParams(prev => ({ ...prev, [param.key]: parseFloat(e.target.value) }))}
              className="w-full bg-elevated border border-white/5 rounded-md px-4 py-2.5 text-white focus:border-accent/30 transition-colors" />
          </div>
        );
      }
      return null;
    });
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link to="/" data-testid="back-to-lobby" className="inline-flex items-center gap-1 text-text-secondary hover:text-accent transition-colors mb-6 text-sm">
        <ArrowLeft className="w-4 h-4" /> Back to Lobby
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-surface rounded-xl border border-white/5 p-6">
            <h1 data-testid="game-title" className="font-heading text-2xl font-bold mb-1">
              {gameInfo?.name || gameId}
            </h1>
            <p className="text-text-secondary text-sm mb-6">{gameInfo?.description}</p>

            <div className="space-y-4">
              <div>
                <label className="text-xs tracking-widest uppercase font-bold text-text-secondary mb-1 block">Bet Amount</label>
                <div className="flex gap-2">
                  <input data-testid="bet-amount" type="number" value={betAmount} min={gameInfo?.min_bet || 1} max={gameInfo?.max_bet || 100000}
                    onChange={e => setBetAmount(parseFloat(e.target.value) || 0)}
                    className="flex-1 bg-elevated border border-white/5 rounded-md px-4 py-2.5 text-white focus:border-accent/30 transition-colors" />
                  <div className="flex gap-1">
                    {[0.5, 2].map(m => (
                      <button key={m} data-testid={`bet-${m}x`} onClick={() => setBetAmount(prev => Math.max(gameInfo?.min_bet || 1, Math.min(gameInfo?.max_bet || 100000, Math.round(prev * m * 100) / 100)))}
                        className="bg-elevated border border-white/5 px-3 py-2 rounded-md text-sm text-text-secondary hover:text-white hover:bg-white/5 transition-colors">
                        {m}x
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {renderParams()}

              {error && <div data-testid="game-error" className="bg-danger/10 border border-danger/20 text-danger text-sm px-4 py-2 rounded-md">{error}</div>}

              <button data-testid="play-btn" onClick={play} disabled={playing}
                className="w-full bg-accent text-black font-bold py-3 rounded-md hover:bg-accent-hover transition-colors shadow-[0_0_15px_rgba(0,231,1,0.3)] disabled:opacity-50 text-lg">
                {playing ? 'Playing...' : `Play - $${betAmount}`}
              </button>
            </div>

            {renderResult()}
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-surface rounded-xl border border-white/5 p-4">
            <h3 className="font-heading text-sm font-semibold mb-3 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-accent" /> Recent Plays
            </h3>
            {history.length === 0 ? (
              <p className="text-text-secondary text-xs">No plays yet</p>
            ) : (
              <div className="space-y-2">
                {history.map((h, i) => (
                  <div key={i} className={`flex items-center justify-between text-xs p-2 rounded-lg ${h.win_amount > h.bet_amount ? 'bg-accent/5' : 'bg-danger/5'}`}>
                    <span className="text-text-secondary">${h.bet_amount}</span>
                    <span className={h.win_amount > h.bet_amount ? 'text-accent font-bold' : 'text-danger'}>
                      {h.multiplier}x / ${h.win_amount}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {gameInfo && (
            <div className="bg-surface rounded-xl border border-white/5 p-4">
              <h3 className="font-heading text-sm font-semibold mb-3">Game Info</h3>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between"><span className="text-text-secondary">Category</span><span>{gameInfo.category}</span></div>
                <div className="flex justify-between"><span className="text-text-secondary">House Edge</span><span>{gameInfo.house_edge}%</span></div>
                <div className="flex justify-between"><span className="text-text-secondary">Min Bet</span><span>${gameInfo.min_bet}</span></div>
                <div className="flex justify-between"><span className="text-text-secondary">Max Bet</span><span>${gameInfo.max_bet}</span></div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
