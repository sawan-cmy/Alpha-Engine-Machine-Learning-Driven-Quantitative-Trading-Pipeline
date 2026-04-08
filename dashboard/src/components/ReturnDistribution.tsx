import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine,
} from 'recharts';
import type { TimeSeriesPoint } from '../types/dashboard';

interface Props {
  data: TimeSeriesPoint[];
}

export const ReturnDistribution: React.FC<Props> = ({ data }) => {
  const buckets = 30;
  const values = data.map((d) => d.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const step = range / buckets;

  const histogram = Array.from({ length: buckets }, (_, i) => {
    const from = min + i * step;
    const to = from + step;
    return {
      label: (from * 100).toFixed(1) + '%',
      count: values.filter((v) => v >= from && v < to).length,
      midpoint: (from + to) / 2,
    };
  });

  return (
    <div className="chart-card">
      <h3 className="chart-title">📊 Daily Return Distribution</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={histogram} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="label"
            tick={{ fill: '#6c7a89', fontSize: 9 }}
            tickLine={false}
            axisLine={false}
            interval={5}
          />
          <YAxis
            tick={{ fill: '#6c7a89', fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            width={32}
          />
          <Tooltip
            contentStyle={{ background: '#1a1a2e', border: '1px solid #333', borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: '#a0aec0' }}
            itemStyle={{ color: '#a29bfe' }}
          />
          <ReferenceLine x={histogram.find((h) => h.midpoint >= 0)?.label} stroke="rgba(255,255,255,0.2)" strokeDasharray="4 4" />
          <Bar dataKey="count" radius={[3, 3, 0, 0]}>
            {histogram.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.midpoint >= 0 ? '#2ed573' : '#ff4757'}
                fillOpacity={0.7}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
