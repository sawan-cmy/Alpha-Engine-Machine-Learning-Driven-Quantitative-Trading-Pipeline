import React from 'react';
import type { ConnectionState } from '../types/live';

interface Props {
  state: ConnectionState;
  lastUpdate: string | null;
}

const STATE_CONFIG: Record<ConnectionState, { label: string; color: string; dot: string }> = {
  connecting:   { label: 'CONNECTING',   color: '#ffa502', dot: '#ffa502' },
  connected:    { label: 'LIVE',         color: '#2ed573', dot: '#2ed573' },
  disconnected: { label: 'RECONNECTING', color: '#ff4757', dot: '#ff4757' },
  error:        { label: 'ERROR',        color: '#ff4757', dot: '#ff4757' },
};

export const ConnectionStatus: React.FC<Props> = ({ state, lastUpdate }) => {
  const cfg = STATE_CONFIG[state];
  const timeStr = lastUpdate
    ? new Date(lastUpdate).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '—';

  return (
    <div className="connection-status">
      <span
        className={`conn-dot ${state === 'connecting' || state === 'disconnected' ? 'conn-dot--blink' : ''}`}
        style={{ background: cfg.dot, boxShadow: `0 0 6px ${cfg.dot}` }}
      />
      <span className="conn-label" style={{ color: cfg.color }}>{cfg.label}</span>
      {state === 'connected' && lastUpdate && (
        <span className="conn-time">Updated {timeStr}</span>
      )}
    </div>
  );
};
