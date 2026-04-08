import lightgbm as lgb
import logging
import numpy as np
import pandas as pd
from cross_validation import PurgedTimeSeriesSplit

class LightGBMModel:
    def __init__(self, config):
        self.params = config.LGBM_PARAMS
        self.n_splits = config.CV_FOLDS
        self.embargo_pct = config.EMBARGO_PCT
        self.cv = PurgedTimeSeriesSplit(n_splits=self.n_splits, embargo_pct=self.embargo_pct)
        self.models = []

    def fit(self, X, y):
        logging.info("Training LightGBM models with Purged Cross Validation...")
        self.models = []
        
        for fold, (train_idx, val_idx) in enumerate(self.cv.split(X)):
            X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
            X_val, y_val = X.iloc[val_idx], y.iloc[val_idx]
            
            train_data = lgb.Dataset(X_train, label=y_train)
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            
            model = lgb.train(
                self.params,
                train_data,
                num_boost_round=500,
                valid_sets=[train_data, val_data],
                callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False),
                           lgb.log_evaluation(period=0)]
            )
            self.models.append(model)
            logging.info(f"Fold {fold+1} Best Iteration: {model.best_iteration}")

    def predict(self, X):
        # Ensemble prediction averaging across all CV models
        if not self.models:
            raise ValueError("Model is not trained yet.")
        
        preds = np.zeros(len(X))
        for model in self.models:
            preds += model.predict(X, num_iteration=model.best_iteration)
        
        return preds / len(self.models)
