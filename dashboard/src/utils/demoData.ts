import type { DashboardData } from '../types/dashboard';

// Fallback / demo data used when no real dashboard_data.json is present
export const DEMO_DATA: DashboardData = {
  generated_at: new Date().toISOString(),
  metrics: {
    Sharpe: 1.42,
    Ann_Return: 0.2315,
    Max_Drawdown: -0.1123,
    Calmar: 2.06,
    Win_Rate: 0.5512,
    Ann_Volatility: 0.1421,
    Total_Trades: 312,
    Profit_Factor: 1.78,
  },
  cum_returns: Array.from({ length: 252 }, (_, i) => {
    const drift = 0.2315 / 252;
    const noise = (Math.random() - 0.5) * 0.02;
    return {
      date: new Date(Date.now() - (252 - i) * 86400000).toISOString().split('T')[0],
      value: parseFloat((1 + (drift + noise) * i).toFixed(4)),
    };
  }),
  drawdowns: Array.from({ length: 252 }, (_, i) => ({
    date: new Date(Date.now() - (252 - i) * 86400000).toISOString().split('T')[0],
    value: parseFloat((-Math.abs(Math.sin(i / 30) * 0.08)).toFixed(4)),
  })),
  net_returns: Array.from({ length: 252 }, (_, i) => ({
    date: new Date(Date.now() - (252 - i) * 86400000).toISOString().split('T')[0],
    value: parseFloat(((Math.random() - 0.48) * 0.025).toFixed(4)),
  })),
  monthly_returns: Array.from({ length: 24 }, (_, i) => ({
    year: 2024 + Math.floor(i / 12),
    month: (i % 12) + 1,
    ret: parseFloat(((Math.random() - 0.45) * 0.06).toFixed(4)),
  })),
  roll_sharpe: Array.from({ length: 252 }, (_, i) => ({
    date: new Date(Date.now() - (252 - i) * 86400000).toISOString().split('T')[0],
    value: parseFloat((1.2 + Math.sin(i / 40) * 0.8 + (Math.random() - 0.5) * 0.3).toFixed(4)),
  })),
};
