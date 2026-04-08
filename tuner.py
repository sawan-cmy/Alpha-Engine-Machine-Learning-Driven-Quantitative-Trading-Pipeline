import lightgbm as lgb
import logging
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from cross_validation import PurgedTimeSeriesSplit
from itertools import product

class HyperparameterTuner:
    def __init__(self, config):
        self.n_splits = config.CV_FOLDS
        self.embargo_pct = config.EMBARGO_PCT
        self.cv = PurgedTimeSeriesSplit(n_splits=self.n_splits, embargo_pct=self.embargo_pct)
        # Search grid
        self.grid = {
            'max_depth': [3, 5],
            'num_leaves': [7, 15],
            'learning_rate': [0.01, 0.05]
        }
    
    def tune(self, X, y):
        logging.info("Starting Hyperparameter Tuning...")
        best_ic = -np.inf
        # Default fallback
        best_params = {
            'objective': 'regression',
            'metric': 'rmse',
            'num_leaves': 15,
            'max_depth': 4,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': 42
        }
        
        keys = self.grid.keys()
        vals = self.grid.values()
        
        for instance in product(*vals):
            params = dict(zip(keys, instance))
            params.update({
                'objective': 'regression',
                'metric': 'rmse',
                'feature_fraction': 0.8,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'verbose': -1,
                'random_state': 42
            })
            
            ic_scores = []
            
            # Cross validation
            for train_idx, val_idx in self.cv.split(X):
                X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
                X_val, y_val = X.iloc[val_idx], y.iloc[val_idx]
                
                train_data = lgb.Dataset(X_train, label=y_train)
                
                # Train small number of rounds for speed in tuning
                model = lgb.train(
                    params,
                    train_data,
                    num_boost_round=100
                )
                
                # Predict on validation
                preds = model.predict(X_val)
                
                # Calculate Information Coefficient (Rank Correlation)
                val_df = pd.DataFrame({'pred': preds, 'target': y_val}, index=X_val.index)
                
                def calc_ic(df):
                    if len(df) > 1:
                        # Use index 0 to support both older and newer scipy versions robustly
                        return spearmanr(df['pred'], df['target'])[0]
                    return 0
                    
                daily_ic = val_df.groupby(level='Date').apply(calc_ic)
                ic_scores.append(daily_ic.mean())
                
            avg_ic = np.nanmean(ic_scores)
            
            # Formatting log nicely
            d = params['max_depth']
            l = params['num_leaves']
            lr = params['learning_rate']
            logging.info(f"Tested params (depth={d}, leaves={l}, lr={lr}) -> Avg IC: {avg_ic:.4f}")
            
            if avg_ic > best_ic:
                best_ic = avg_ic
                best_params = params.copy()
                
        logging.info(f"Best IC achieved: {best_ic:.4f}")
        return best_params
