import pandas as pd
import numpy as np
import logging

class Backtester:
    def __init__(self, config):
        self.tc = config.TRANSACTION_COST_BPS / 10000.0
        self.horizon = config.TARGET_HORIZON_DAYS

    def run(self, df_prices, weights):
        """
        df_prices: MultiIndex DataFrame with 'Close'
        weights: Series with MultiIndex (Date, Ticker) representing target allocations at Close
        """
        logging.info("Running vectorized backtest...")
        
        # Unstack to get wide format [Date, Tickers]
        close_px = df_prices['Close'].unstack(level=1)
        w_wide = weights.unstack(level=1).fillna(0)
        
        # Shift returns to simulate entering at Close(T) and realizing return at Close(T+1)
        daily_returns = close_px.pct_change(fill_method=None).shift(-1)
        
        # Portfolio return
        port_returns = (w_wide * daily_returns).sum(axis=1)
        
        # Turnover calculation (change in weights)
        turnover = w_wide.diff().abs().sum(axis=1)
        
        # Transaction costs drag
        tc_drag = turnover * self.tc
        
        net_returns = port_returns - tc_drag
        
        # Remove the final NaNs due to shift
        net_returns = net_returns.dropna()
        
        return self._calculate_metrics(net_returns, turnover)

    def _calculate_metrics(self, returns, turnover):
        metrics = {}
        ann_factor = 252
        
        compounded_return = (1 + returns).prod() - 1
        years = len(returns) / ann_factor
        metrics['Ann_Return'] = (1 + compounded_return) ** (1 / years) - 1 if years > 0 else 0
        
        metrics['Ann_Vol'] = returns.std() * np.sqrt(ann_factor)
        
        metrics['Sharpe'] = metrics['Ann_Return'] / metrics['Ann_Vol'] if metrics['Ann_Vol'] > 0 else 0
        
        cum_returns = (1 + returns).cumprod()
        rolling_max = cum_returns.cummax()
        drawdown = cum_returns / rolling_max - 1
        metrics['Max_Drawdown'] = drawdown.min()
        
        metrics['Calmar'] = metrics['Ann_Return'] / abs(metrics['Max_Drawdown']) if metrics['Max_Drawdown'] < 0 else 0
        
        metrics['Avg_Daily_Turnover'] = turnover.mean()
        
        return metrics, cum_returns, returns

