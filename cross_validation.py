import numpy as np

class PurgedTimeSeriesSplit:
    def __init__(self, n_splits=5, embargo_pct=0.02):
        self.n_splits = n_splits
        self.embargo_pct = embargo_pct
        
    def split(self, X, y=None, groups=None):
        """
        Generate indices to split data into training and test set.
        Assumes X is sorted by time.
        """
        n_samples = len(X)
        fold_size = int(n_samples / self.n_splits)
        embargo_size = int(n_samples * self.embargo_pct)
        
        indices = np.arange(n_samples)
        
        for i in range(self.n_splits - 1):
            train_end = (i + 1) * fold_size
            test_start = train_end + embargo_size
            
            # If embargo pushes test_start past the end, break
            if test_start >= n_samples:
                break
                
            # The test set goes to the end of the next fold, or end of data
            test_end = min(test_start + fold_size, n_samples)
            
            # Simple walk-forward: train on everything up to train_end
            # In a more strict setup, we would only train on rolling window, but expanding window is fine here
            yield indices[:train_end], indices[test_start:test_end]
