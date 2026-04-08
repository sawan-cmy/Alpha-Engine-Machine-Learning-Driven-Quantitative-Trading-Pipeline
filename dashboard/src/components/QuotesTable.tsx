import React from 'react';
import type { QuoteData } from '../types/live';

interface Props {
  quotes: Record<string, QuoteData>;
}

function fmtPrice(v: number | null): string {
  if (v === null) return '—';
  return `₹${v >= 1000 ? v.toLocaleString('en-IN', { maximumFractionDigits: 2 }) : v.toFixed(2)}`;
}

function fmtPct(v: number | null): string {
  if (v === null) return '—';
  return `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
}

function fmtVol(v: number | null): string {
  if (v === null) return '—';
  if (v >= 1e7) return `${(v / 1e7).toFixed(2)} Cr`;
  if (v >= 1e5) return `${(v / 1e5).toFixed(2)} L`;
  return v.toLocaleString('en-IN');
}

function fmtSource(src: string): React.ReactNode {
  const isOpenBB = src.toLowerCase().includes('openbb');
  const style: React.CSSProperties = isOpenBB
    ? { color: '#a29bfe', fontWeight: 700, fontSize: 10, letterSpacing: '0.5px' }
    : { color: '#6c7a89', fontSize: 10 };
  return <span style={style}>{isOpenBB ? '⚛ OpenBB' : src}</span>;
}

const QuoteRow: React.FC<{ q: QuoteData }> = ({ q }) => {
  const isUp    = (q.change_pct ?? 0) >= 0;
  const hasData = q.price !== null;
  const color   = hasData ? (isUp ? '#2ed573' : '#ff4757') : '#6c7a89';

  return (
    <div className="quote-row">
      <div className="quote-row-id">
        <span className="quote-display">{q.display}</span>
        <span className="quote-sector">{q.sector}</span>
      </div>
      <span className="quote-price" style={{ color }}>{fmtPrice(q.price)}</span>
      <span className="quote-change" style={{ color }}>
        {hasData ? `${isUp ? '▲' : '▼'} ${fmtPct(q.change_pct)}` : '—'}
      </span>
      <span className="quote-highlow">
        <span style={{ color: '#2ed573' }}>{fmtPrice(q.high)}</span>
        {' / '}
        <span style={{ color: '#ff4757' }}>{fmtPrice(q.low)}</span>
      </span>
      <span className="quote-volume">{fmtVol(q.volume)}</span>
      <span className="quote-source">{fmtSource(q.source)}</span>
    </div>
  );
};

export const QuotesTable: React.FC<Props> = ({ quotes }) => {
  const rows = Object.values(quotes);

  return (
    <div className="chart-card quotes-table-card">
      <h3 className="chart-title">🏛️ Market Snapshot — NSE Watchlist</h3>
      <div className="quotes-header">
        <span>Symbol</span>
        <span>Price</span>
        <span>Change</span>
        <span>High / Low</span>
        <span>Volume</span>
        <span>Source</span>
      </div>
      <div className="quotes-body">
        {rows.map((q) => <QuoteRow key={q.symbol} q={q} />)}
      </div>
    </div>
  );
};
