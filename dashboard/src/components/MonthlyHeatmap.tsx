import React, { useMemo } from 'react';
import type { MonthlyReturn } from '../types/dashboard';

interface Props {
  data: MonthlyReturn[];
}

const MONTH_LABELS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

function getColor(value: number): string {
  const intensity = Math.min(Math.abs(value) / 0.08, 1);
  if (value >= 0) {
    const g = Math.round(100 + intensity * 155);
    const alpha = 0.2 + intensity * 0.7;
    return `rgba(46, ${g}, 115, ${alpha})`;
  } else {
    const r = Math.round(150 + intensity * 105);
    const alpha = 0.2 + intensity * 0.7;
    return `rgba(${r}, 71, 87, ${alpha})`;
  }
}

export const MonthlyHeatmap: React.FC<Props> = ({ data }) => {
  const { years, pivot } = useMemo(() => {
    const yrs = [...new Set(data.map((d) => d.year))].sort();
    const piv: Record<number, Record<number, number>> = {};
    data.forEach(({ year, month, ret }) => {
      if (!piv[year]) piv[year] = {};
      piv[year][month] = ret;
    });
    return { years: yrs, pivot: piv };
  }, [data]);

  return (
    <div className="chart-card heatmap-card">
      <h3 className="chart-title">📅 Monthly Returns Heatmap</h3>
      <div className="heatmap-wrapper">
        <table className="heatmap-table">
          <thead>
            <tr>
              <th className="heatmap-year-label">Year</th>
              {MONTH_LABELS.map((m) => (
                <th key={m} className="heatmap-month-label">{m}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {years.map((year) => (
              <tr key={year}>
                <td className="heatmap-year">{year}</td>
                {Array.from({ length: 12 }, (_, i) => i + 1).map((month) => {
                  const val = pivot[year]?.[month];
                  return (
                    <td
                      key={month}
                      className="heatmap-cell"
                      style={{ background: val !== undefined ? getColor(val) : 'transparent' }}
                      title={val !== undefined ? `${(val * 100).toFixed(2)}%` : 'No data'}
                    >
                      {val !== undefined ? (
                        <span style={{ color: Math.abs(val) > 0.04 ? '#fff' : '#ccc' }}>
                          {(val * 100).toFixed(1)}%
                        </span>
                      ) : (
                        <span style={{ color: '#333' }}>—</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
