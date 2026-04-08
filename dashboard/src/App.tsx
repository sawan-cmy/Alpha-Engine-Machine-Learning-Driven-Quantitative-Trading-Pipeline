import React, { useCallback, useEffect, useState } from 'react';
import type { WsMessage, QuoteData, ConnectionState } from './types/live';
import type { DashboardData } from './types/dashboard';
import { useWebSocket } from './hooks/useWebSocket';
import { loadDashboardData } from './utils/dataLoader';
import { DEMO_DATA } from './utils/demoData';

import { Header }              from './components/Header';
import { TickerBar }           from './components/TickerBar';
import { ConnectionStatus }    from './components/ConnectionStatus';
import { LivePriceChart }      from './components/LivePriceChart';
import { QuotesTable }         from './components/QuotesTable';
import { MetricsGrid }         from './components/MetricsGrid';
import { TimeSeriesChart }     from './components/TimeSeriesChart';
import { MonthlyHeatmap }      from './components/MonthlyHeatmap';
import { ReturnDistribution }  from './components/ReturnDistribution';

const DEFAULT_SYMBOL = 'RELIANCE.NS';
const NSE_SYMBOLS = [
  '^NSEI','RELIANCE.NS','TCS.NS','INFY.NS','HDFCBANK.NS',
  'ICICIBANK.NS','HINDUNILVR.NS','BHARTIARTL.NS','ITC.NS','SBIN.NS',
];

// Fallback empty quotes while WS loads
function emptyQuotes(): Record<string, QuoteData> {
  return Object.fromEntries(NSE_SYMBOLS.map((sym) => [
    sym, {
      symbol: sym, display: sym, sector: '', price: null,
      change: null, change_pct: null, volume: null,
      high: null, low: null, open: null, prev_close: null,
      market_cap: null, updated_at: new Date().toISOString(), source: 'none',
    } satisfies QuoteData,
  ]));
}

const App: React.FC = () => {
  // ── Live market state ──────────────────────────────────────────────────────
  const [quotes, setQuotes]           = useState<Record<string, QuoteData>>(emptyQuotes());
  const [wsState, setWsState]         = useState<ConnectionState>('connecting');
  const [lastUpdate, setLastUpdate]   = useState<string | null>(null);
  const [selectedSym, setSelectedSym] = useState<string>(DEFAULT_SYMBOL);

  // ── Strategy metrics state ─────────────────────────────────────────────────
  const [strategyData, setStrategyData] = useState<DashboardData | null>(null);
  const [isDemo, setIsDemo]             = useState(false);

  // ── WS message handler ─────────────────────────────────────────────────────
  const handleMessage = useCallback((msg: WsMessage) => {
    if (msg.type === 'quote_update') {
      setQuotes((prev) => ({ ...prev, ...msg.data }));
      setLastUpdate(msg.timestamp);
    }
  }, []);

  const { state } = useWebSocket({ onMessage: handleMessage });
  useEffect(() => setWsState(state), [state]);

  // ── Strategy data (from JSON or demo) ─────────────────────────────────────
  useEffect(() => {
    loadDashboardData().then((d) => {
      setStrategyData(d);
      setIsDemo(d === DEMO_DATA);
    });
  }, []);

  // ── If WS is down, poll REST as fallback ─────────────────────────────────
  useEffect(() => {
    if (wsState !== 'disconnected' && wsState !== 'error') return;
    const id = setInterval(async () => {
      try {
        const res = await fetch('http://localhost:8000/api/quotes');
        if (!res.ok) return;
        const json = await res.json();
        setQuotes((prev) => ({ ...prev, ...json.data }));
        setLastUpdate(new Date().toISOString());
      } catch { /* backend offline */ }
    }, 30_000);
    return () => clearInterval(id);
  }, [wsState]);

  const activeQuotes = Object.fromEntries(
    Object.entries(quotes).filter(([, q]) => q.price !== null)
  );
  const hasLiveData = Object.values(quotes).some((q) => q.price !== null);

  return (
    <div className="app">
      {/* ── Sticky header ── */}
      <Header generatedAt={strategyData?.generated_at ?? new Date().toISOString()} isDemo={isDemo} />

      {/* ── Live ticker bar ── */}
      <TickerBar quotes={hasLiveData ? activeQuotes : quotes} />

      <main className="dashboard-main">
        {/* ── Connection status + live price section ── */}
        <section className="live-section">
          <div className="section-header">
            <h2>📡 Real-Time Market Data</h2>
            <ConnectionStatus state={wsState} lastUpdate={lastUpdate} />
          </div>

          {/* Symbol price chart */}
          <LivePriceChart
            quotes={quotes}
            selectedSymbol={selectedSym}
            onSelectSymbol={setSelectedSym}
          />

          {/* Market snapshot table */}
          <QuotesTable quotes={quotes} />
        </section>

        {/* ── Divider ── */}
        <div className="section-divider">
          <span>Strategy Analytics</span>
        </div>

        {/* ── Strategy performance (from Python pipeline) ── */}
        {strategyData && (
          <>
            <MetricsGrid metrics={strategyData.metrics} />

            <div className="charts-grid-full">
              <TimeSeriesChart
                title="📈 Cumulative Returns (Wealth Index)"
                data={strategyData.cum_returns}
                color="#00d4ff" gradientId="gradCum"
                yTickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
              />
            </div>

            <div className="charts-grid-full">
              <TimeSeriesChart
                title="📉 Drawdowns (Underwater Curve)"
                data={strategyData.drawdowns}
                color="#ff4757" gradientId="gradDD"
                referenceLineY={0} isNegative
                yTickFormatter={(v) => `${(v * 100).toFixed(1)}%`}
              />
            </div>

            <div className="charts-grid-half">
              <TimeSeriesChart
                title="⚡ Rolling 252-Day Sharpe Ratio"
                data={strategyData.roll_sharpe}
                color="#ffa502" gradientId="gradSharpe"
                referenceLineY={0}
                yTickFormatter={(v) => v.toFixed(2)}
              />
              <ReturnDistribution data={strategyData.net_returns} />
            </div>

            <div className="charts-grid-full">
              <MonthlyHeatmap data={strategyData.monthly_returns} />
            </div>
          </>
        )}
      </main>

      <footer className="dashboard-footer">
        <span>AlphaEngine Pipeline · OpenBB Platform + FastAPI + React TypeScript · For institutional use only</span>
      </footer>
    </div>
  );
};

export default App;
