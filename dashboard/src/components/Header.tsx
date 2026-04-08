import React from 'react';

interface Props {
  generatedAt: string;
  isDemo: boolean;
}

export const Header: React.FC<Props> = ({ generatedAt, isDemo }) => {
  const date = new Date(generatedAt);
  const formatted = isNaN(date.getTime()) ? '—' : date.toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });

  return (
    <header className="dashboard-header">
      <div className="header-logo">
        <span className="logo-icon">⚛</span>
        <div className="logo-text">
          <span className="logo-main">ALPHA ENGINE</span>
          <span className="logo-sub">DASHBOARD</span>
        </div>
      </div>
      <div className="header-meta">
        {isDemo && (
          <span className="demo-badge">⚠ Demo Data</span>
        )}
        <span className="header-generated">Generated: {formatted}</span>
      </div>
      <div className="header-pulse">
        <span className="pulse-dot" />
        <span className="pulse-label">LIVE ANALYSIS</span>
      </div>
    </header>
  );
};
