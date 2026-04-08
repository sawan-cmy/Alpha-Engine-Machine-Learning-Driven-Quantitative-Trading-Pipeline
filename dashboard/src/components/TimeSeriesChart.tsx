import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import type { TimeSeriesPoint } from '../types/dashboard';

interface Props {
  data: TimeSeriesPoint[];
  title: string;
  color: string;
  fillOpacity?: number;
  yTickFormatter?: (v: number) => string;
  referenceLineY?: number;
  gradientId: string;
  isNegative?: boolean;
}

const CustomTooltip: React.FC<{ active?: boolean; payload?: any[]; label?: string; color: string }> = ({ active, payload, label, color }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <p className="tooltip-date">{label}</p>
      <p className="tooltip-val" style={{ color }}>{payload[0].value?.toFixed(4)}</p>
    </div>
  );
};

export const TimeSeriesChart: React.FC<Props> = ({
  data, title, color, yTickFormatter, referenceLineY, gradientId, isNegative,
}) => {
  // Thin out data for performance — keep max 120 points
  const step = Math.max(1, Math.floor(data.length / 120));
  const thinned = data.filter((_, i) => i % step === 0);

  return (
    <div className="chart-card">
      <h3 className="chart-title">{title}</h3>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={thinned} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={isNegative ? 0.3 : 0.4} />
              <stop offset="95%" stopColor={color} stopOpacity={0.01} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#6c7a89', fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(d) => d?.substring(5)}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fill: '#6c7a89', fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={yTickFormatter ?? ((v) => v.toFixed(2))}
            width={52}
          />
          <Tooltip content={<CustomTooltip color={color} />} />
          {referenceLineY !== undefined && (
            <ReferenceLine y={referenceLineY} stroke="rgba(255,255,255,0.2)" strokeDasharray="4 4" />
          )}
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            fill={`url(#${gradientId})`}
            dot={false}
            activeDot={{ r: 4, fill: color, stroke: '#0f0f0f', strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
