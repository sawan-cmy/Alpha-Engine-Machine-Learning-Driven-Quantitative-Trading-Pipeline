import React, { useEffect, useState } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { QuoteData, OhlcvPoint } from '../types/live';

interface Props {
  quotes: Record<string, QuoteData>;
  selectedSymbol: string;
  onSelectSymbol: (sym: string) => void;
}

const API = 'http://localhost:8000';

function fmtPrice(v: number | null): string {
  if (v === null) return '—';
  return v >= 1000 ? v.toLocaleString('en-IN', { maximumFractionDigits: 2 }) : v.toFixed(2);
}

const CustomTooltip: React.FC<{ active?: boolean; payload?: any[]; label?: string }> = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload as OhlcvPoint;
  return (
    <div className="chart-tooltip">
      <p className="tooltip-date">{label}</p>
      <div className="ohlcv-tooltip">
        <span style={{ color: '#a0aec0' }}>O</span> <b>{fmtPrice(d.open)}</b>{' '}
        <span style={{ color: '#a0aec0' }}>H</span> <b style={{ color: '#2ed573' }}>{fmtPrice(d.high)}</b>{' '}
        <span style={{ color: '#a0aec0' }}>L</span> <b style={{ color: '#ff4757' }}>{fmtPrice(d.low)}</b>{' '}
        <span style={{ color: '#a0aec0' }}>C</span> <b style={{ color: '#00d4ff' }}>{fmtPrice(d.close)}</b>
      </div>
    </div>
  );
};

export const LivePriceChart: React.FC<Props> = ({ quotes, selectedSymbol, onSelectSymbol }) => {
  const [history, setHistory] = useState<OhlcvPoint[]>([]);
  const [loading, setLoading] = useState(false);

  const quote = quotes[selectedSymbol];

  useEffect(() => {
    if (!selectedSymbol) return;
    setLoading(true);
    fetch(`${API}/api/history/${encodeURIComponent(selectedSymbol)}?days=365`)
      .then((r) => r.json())
      .then((j) => {
        setHistory(j.data ?? []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [selectedSymbol]);

  // Live price appended to history tail
  const chartData: OhlcvPoint[] = history.length
    ? [...history.slice(-120)]  // last 120 sessions
    : [];

  const isUp = (quote?.change_pct ?? 0) >= 0;
  const chartColor = isUp ? '#2ed573' : '#ff4757';

  const symbols = Object.keys(quotes);

  return (
    <div className="chart-card live-chart-card">
      {/* Symbol selector tabs */}
      <div className="symbol-tabs">
        {symbols.map((sym) => {
          const q = quotes[sym];
          const up = (q?.change_pct ?? 0) >= 0;
          return (
            <button
              key={sym}
              onClick={() => onSelectSymbol(sym)}
              className={`symbol-tab ${sym === selectedSymbol ? 'symbol-tab--active' : ''}`}
            >
              <span className="tab-name">{q?.display ?? sym}</span>
              {q?.price !== null && (
                <span className="tab-price" style={{ color: up ? '#2ed573' : '#ff4757' }}>
                  {up ? '▲' : '▼'} {q?.change_pct?.toFixed(2)}%
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Hero price block */}
      {quote && (
        <div className="live-hero">
          <div className="live-hero-left">
            <span className="live-symbol-name">{quote.display}</span>
            <span className="live-sector">{quote.sector}</span>
          </div>
          <div className="live-hero-right">
            <span className="live-price" style={{ color: chartColor }}>
              ₹{fmtPrice(quote.price)}
            </span>
            <span className="live-change" style={{ color: chartColor }}>
              {(quote.change ?? 0) >= 0 ? '+' : ''}{fmtPrice(quote.change)}{' '}
              ({(quote.change_pct ?? 0) >= 0 ? '+' : ''}{quote.change_pct?.toFixed(2) ?? '—'}%)
            </span>
          </div>
          <div className="live-stats">
            <div className="live-stat"><span>Open</span><b>₹{fmtPrice(quote.open)}</b></div>
            <div className="live-stat"><span>High</span><b style={{ color: '#2ed573' }}>₹{fmtPrice(quote.high)}</b></div>
            <div className="live-stat"><span>Low</span><b style={{ color: '#ff4757' }}>₹{fmtPrice(quote.low)}</b></div>
            <div className="live-stat"><span>Prev</span><b>₹{fmtPrice(quote.prev_close)}</b></div>
          </div>
        </div>
      )}

      {/* Price history chart */}
      <h3 className="chart-title" style={{ marginTop: 12 }}>
        📈 1-Year Price History{loading ? ' (loading…)' : ''}
      </h3>
      {loading ? (
        <div className="chart-loading"><div className="spinner" /></div>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="liveGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={chartColor} stopOpacity={0.4} />
                <stop offset="95%" stopColor={chartColor} stopOpacity={0.01} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis
              dataKey="date"
              tick={{ fill: '#6c7a89', fontSize: 10 }}
              tickLine={false} axisLine={false}
              tickFormatter={(d) => d?.substring(5)}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fill: '#6c7a89', fontSize: 10 }}
              tickLine={false} axisLine={false}
              tickFormatter={(v) => `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
              width={70}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone" dataKey="close"
              stroke={chartColor} strokeWidth={2}
              fill="url(#liveGrad)" dot={false}
              activeDot={{ r: 4, fill: chartColor, stroke: '#0f0f0f', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};
