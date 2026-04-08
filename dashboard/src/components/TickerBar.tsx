import React, { useRef } from 'react';
import type { QuoteData } from '../types/live';

interface Props {
  quotes: Record<string, QuoteData>;
}

function fmtPrice(v: number | null): string {
  if (v === null) return '—';
  return v >= 1000 ? v.toLocaleString('en-IN', { maximumFractionDigits: 2 }) : v.toFixed(2);
}

function fmtPct(v: number | null): string {
  if (v === null) return '—';
  return `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`;
}

const TickerItem: React.FC<{ q: QuoteData }> = ({ q }) => {
  const isUp    = (q.change_pct ?? 0) >= 0;
  const hasData = q.price !== null;

  return (
    <span className={`ticker-item ${hasData ? (isUp ? 'ticker-item--up' : 'ticker-item--down') : 'ticker-item--neutral'}`}>
      <span className="ticker-symbol">{q.display}</span>
      <span className="ticker-price">{fmtPrice(q.price)}</span>
      {hasData && (
        <span className="ticker-change">
          {isUp ? '▲' : '▼'} {fmtPct(q.change_pct)}
        </span>
      )}
      <span className="ticker-sep">·</span>
    </span>
  );
};

export const TickerBar: React.FC<Props> = ({ quotes }) => {
  const trackRef = useRef<HTMLDivElement>(null);
  const items = Object.values(quotes);

  // Duplicate items for seamless infinite scroll
  const doubled = [...items, ...items];

  return (
    <div className="ticker-bar" aria-label="Live price ticker">
      <span className="ticker-label">⚡ LIVE</span>
      <div className="ticker-track-wrapper">
        <div className="ticker-track" ref={trackRef}>
          {doubled.map((q, i) => (
            <TickerItem key={`${q.symbol}-${i}`} q={q} />
          ))}
        </div>
      </div>
    </div>
  );
};
