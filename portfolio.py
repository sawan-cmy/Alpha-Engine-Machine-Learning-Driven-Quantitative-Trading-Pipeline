import pandas as pd
import numpy as np

class PortfolioConstructor:
    def __init__(self, config):
        self.max_long = config.MAX_LONG_WEIGHT
        self.max_short = config.MAX_SHORT_WEIGHT

    def generate_weights(self, df_with_preds):
        """
        df_with_preds: DataFrame with MultiIndex (Date, Ticker) and column 'prediction'
        """
        weights = pd.Series(index=df_with_preds.index, dtype=float)
        
        # Calculate cross-sectional ranks each day to avoid broad market exposure
        for date, group in df_with_preds.groupby(level='Date'):
            preds = group['prediction']
            
            # Simple rank-based long/short:
            # Demean to be market neutral, scale sum of absolute weights to 1.0
            if len(preds) > 1:
                demeaned = preds - preds.mean()
                abs_sum = demeaned.abs().sum()
                if abs_sum > 0:
                    w = demeaned / abs_sum
                else:
                    w = pd.Series(0, index=preds.index)
            else:
                w = pd.Series(0, index=preds.index)
                
            # Apply individual position limits
            w = w.clip(lower=self.max_short, upper=self.max_long)
            
            # Re-normalize after clipping to ensure gross leverage <= 1.0
            abs_sum = w.abs().sum()
            if abs_sum > 1.0:
                w = w / abs_sum
                
            weights.loc[date] = w.values
            
        return weights
