import React from 'react';
import { fmtPct, fmtNum } from '../utils/dataLoader';
import type { Metrics } from '../types/dashboard';

interface Props {
  metrics: Metrics;
}


interface KpiCardProps {
  label: string;
  value: string;
  color: string;
  icon: string;
  positive?: boolean;
}

const KpiCard: React.FC<KpiCardProps> = ({ label, value, color, icon, positive }) => (
  <div className="kpi-card" style={{ '--accent': color } as React.CSSProperties}>
    <div className="kpi-icon">{icon}</div>
    <div className="kpi-body">
      <span className="kpi-label">{label}</span>
      <span className="kpi-value" style={{ color: positive === undefined ? color : positive ? '#2ed573' : '#ff4757' }}>
        {value}
      </span>
    </div>
  </div>
);

export const MetricsGrid: React.FC<Props> = ({ metrics }) => {
  const deploy = metrics.Sharpe > 0.5 && metrics.Max_Drawdown > -0.15
    ? { label: '✅ PAPER TRADE', color: '#2ed573' }
    : { label: '🔁 REVIEW EDGE', color: '#ffa502' };

  return (
    <section className="metrics-section">
      <div className="section-header">
        <h2>📊 Strategy Metrics</h2>
        <span className="badge" style={{ background: deploy.color + '22', color: deploy.color, border: `1px solid ${deploy.color}` }}>
          {deploy.label}
        </span>
      </div>
      <div className="kpi-grid">
        <KpiCard label="Sharpe Ratio"     value={fmtNum(metrics.Sharpe)}        color="#00d4ff" icon="⚡" />
        <KpiCard label="Ann. Return"      value={fmtPct(metrics.Ann_Return)}    color="#2ed573" icon="📈" positive={metrics.Ann_Return > 0} />
        <KpiCard label="Max Drawdown"     value={fmtPct(metrics.Max_Drawdown)}  color="#ff4757" icon="📉" positive={false} />
        <KpiCard label="Calmar Ratio"     value={fmtNum(metrics.Calmar)}        color="#a29bfe" icon="🎯" />
        <KpiCard label="Ann. Volatility"  value={fmtPct(metrics.Ann_Volatility ?? 0)} color="#fd79a8" icon="📊" />
        <KpiCard label="Avg Turnover"     value={fmtPct(metrics.Avg_Daily_Turnover ?? 0)} color="#55efc4" icon="🔁" />
      </div>
    </section>
  );
};
