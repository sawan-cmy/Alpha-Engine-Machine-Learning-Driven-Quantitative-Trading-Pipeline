export interface TimeSeriesPoint {
  date: string;
  value: number;
}

export interface MonthlyReturn {
  year: number;
  month: number;
  ret: number;
}

export interface Metrics {
  Sharpe: number;
  Ann_Return: number;
  Max_Drawdown: number;
  Calmar: number;
  Ann_Volatility?: number;
  Avg_Daily_Turnover?: number;
}

export interface DashboardData {
  cum_returns: TimeSeriesPoint[];
  drawdowns: TimeSeriesPoint[];
  net_returns: TimeSeriesPoint[];
  monthly_returns: MonthlyReturn[];
  roll_sharpe: TimeSeriesPoint[];
  metrics: Metrics;
  generated_at: string;
}
