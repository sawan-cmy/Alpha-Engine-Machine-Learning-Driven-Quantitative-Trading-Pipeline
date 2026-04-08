# config.py

# Universe definition (Highly liquid Indian large-cap equities - Nifty 50 constituents)
UNIVERSE = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS',
    'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'LT.NS', 'BAJFINANCE.NS',
    'KOTAKBANK.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'HCLTECH.NS', 'TITAN.NS',
    'MARUTI.NS', 'SUNPHARMA.NS', 'TATASTEEL.NS', 'ULTRACEMCO.NS', 'HINDUNILVR.NS',
    'TATAMOTORS.NS', 'BAJAJFINSV.NS', 'M&M.NS', 'ONGC.NS', 'WIPRO.NS',
    'NTPC.NS', 'JSWSTEEL.NS', 'POWERGRID.NS', 'ADANIENT.NS', 'INDUSINDBK.NS'
]

# Time horizon
START_DATE = '2015-01-01'
END_DATE = '2024-01-01'

# Feature & Target Parameters
TARGET_HORIZON_DAYS = 5
VOLATILITY_WINDOW = 20

# Trading & Portfolio Constraints
TRANSACTION_COST_BPS = 5.0 # 5 basis points (0.05%) round-trip
MAX_LONG_WEIGHT = 0.15     # Max exposure to a single asset
MAX_SHORT_WEIGHT = -0.15

# Machine Learning Parameters
LGBM_PARAMS = {
    'objective': 'regression',
    'metric': 'rmse',
    'num_leaves': 15,          # Heavily constrained
    'max_depth': 4,            # Prevent overfitting
    'learning_rate': 0.05,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'verbose': -1,
    'random_state': 42
}

CV_FOLDS = 4
EMBARGO_PCT = 0.02 # 2% of data length dropped between train and val
