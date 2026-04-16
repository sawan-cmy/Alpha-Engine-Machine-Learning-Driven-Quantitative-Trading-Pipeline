# Alpha Engine — ML-Driven Quantitative Trading Research Pipeline

---

## Overview

Alpha Engine is a Python-based, end-to-end quantitative research pipeline built for systematic
signal generation and backtesting on Indian equities. It is not a live trading system and
makes no claim of profitability. The goal was to build something that covers the full research
loop correctly: clean data ingestion, time-series-safe feature engineering, model training
with proper cross-validation, portfolio construction, and realistic backtesting with transaction
costs.

The universe is approximately 40 highly liquid Nifty 50 stocks, traded on NSE, with price
history from 2015 to 2024 sourced from Yahoo Finance via `yfinance`.

Results from the pipeline are exported as JSON and rendered in a locally hosted React dashboard
(Vite frontend + FastAPI backend).

---

## System Architecture

```
+-----------------+
|   config.py     |  Universe, dates, model params, risk limits, cost assumptions
+-----------------+
        |
        v
+-----------------+
|  data_loader.py |  yfinance download -> OHLCV -> MultiIndex (Date, Ticker) DataFrame
+-----------------+
        |
        v
+-----------------+
|   factors.py    |  7 cross-sectional features, rank-normalized per day
+-----------------+
        |
        v
+-------------------+      +---------------------+
|    tuner.py       |      | cross_validation.py |
|  Grid search over |----->| PurgedTimeSeriesSplit|
|  IC across folds  |      | + embargo gap        |
+-------------------+      +---------------------+
        |
        v
+-----------------+
|    model.py     |  LightGBM, trained per CV fold, ensemble-averaged prediction
+-----------------+
        |
        v
+-----------------+
|  portfolio.py   |  Demeaned signal -> long/short weights, position capped at ±15%
+-----------------+
        |
        v
+-----------------+
|   backtest.py   |  Daily P&L simulation, transaction cost drag, key metrics
+-----------------+
        |
        v
+----------------------+
|  visualization.py    |  Writes dashboard_data.json; generates HTML tearsheet
+----------------------+
        |
        v
+-------------------------------+
|  FastAPI backend (port 8000)  |  Serves JSON to React UI
|  Vite/React frontend (5173)   |  Renders equity curve, metrics
+-------------------------------+
```

All stages are orchestrated sequentially by `main.py`.

---

## Data Assumptions

- **Source:** Yahoo Finance via `yfinance`. Fields used: `Close`, `High`, `Low`, `Volume`.
- **Storage format:** Long-format MultiIndex DataFrame with levels `(Date, Ticker)`.
- **Missing data:** Forward-filled within each ticker on trading days. Remaining NaNs
  (i.e., rows before a stock existed) are dropped.
- **Survivorship bias:** Present. Only currently listed constituents are included. Stocks
  that were delisted between 2015 and 2024 are absent. This inflates backtest results to
  an unknown degree.
- **Adjusted prices:** Yahoo Finance provides adjusted close prices for splits and dividends.
  `High` and `Low` are not adjusted — this is a known imprecision in the intraday volatility
  factor calculation.
- **Time range:** 2015-01-01 to 2024-01-01. Approximately 9 years of daily data.

---

## Feature Engineering

All features are computed in `factors.py`. The target and all features are aligned to the
same timestamp to avoid look-ahead bias.

### Target

```
forward_return(t) = Close(t + 5) / Close(t) - 1
```

This is the 5-day forward return, shifted backwards onto the current row. Rows near the
end of the series where `t + 5` does not exist are dropped via `dropna()`.

### Features

| Feature         | Description                                             |
|-----------------|---------------------------------------------------------|
| `vol_20d`       | 20-day rolling std of daily returns                     |
| `mom_1m`        | 21-day price momentum                                   |
| `mom_3m`        | 63-day price momentum                                   |
| `mom_6m`        | 126-day price momentum                                  |
| `reversal_1w`   | Negated 5-day return (short-term mean-reversion proxy)  |
| `volume_shock`  | Today's volume / 20-day rolling average volume          |
| `intraday_vol`  | (High - Low) / Close — normalized daily range           |

### Cross-Sectional Normalization

Every feature is rank-normalized cross-sectionally each day (across all tickers in the
universe) and rescaled to `[-1, 1]`. This removes market-wide trends from the signal,
helps with stationarity, and reduces sensitivity to outliers.

```python
factors[col] = factors.groupby(level='Date')[col].transform(
    lambda x: (x.rank() - 1) / (len(x) - 1) * 2 - 1 if len(x) > 1 else 0
)
```

---

## Models

### LightGBM (Gradient Boosted Trees)

- **Task:** Regression on 5-day forward returns
- **Library:** `lightgbm >= 4.0.0`
- **Regularization:** Constrained tree depth (`max_depth=4`), limited leaves (`num_leaves=15`),
  feature and bagging subsampling (`0.8` fraction each)
- **Training:** Up to 500 boosting rounds with early stopping (50 rounds patience)
- **Ensemble:** One model is trained per CV fold. Final predictions are the arithmetic mean
  across all fold models. This is a simple way to reduce variance without a full stacking setup.

### Hyperparameter Tuning

Grid search is run before final training (`tuner.py`). The search space is small by design:

```
max_depth:     [3, 5]
num_leaves:    [7, 15]
learning_rate: [0.01, 0.05]
```

Each combination is evaluated using mean daily **Information Coefficient (IC)** — the
Spearman rank correlation between predicted and realized forward returns, averaged across
dates in the validation fold. IC is the standard signal quality metric in cross-sectional
equity research. The best parameter set is injected into `config.LGBM_PARAMS` before
final model training.

---

## Cross-Validation: Purged Time-Series Split

Standard k-fold cross-validation leaks future data into training when applied to time
series. The `PurgedTimeSeriesSplit` class in `cross_validation.py` addresses this with two
mechanisms:

1. **Walk-forward structure:** Training always uses data from the past only (expanding window).
   Validation is always the immediately following block.

2. **Embargo period:** A gap of `embargo_pct = 2%` of total samples is dropped between the
   end of training and the start of validation. This prevents leakage from overlapping
   forward-return labels — since the target is a 5-day forward return, the last few rows of
   the training set share return information with the first rows of the validation set.

```
|---- TRAIN ----|-- embargo --|---- VALIDATION ----|
```

With `CV_FOLDS = 4`, three train/validation splits are generated (the last fold has no
subsequent block for validation).

---

## Backtesting Methodology

Backtesting is implemented in `backtest.py` as a vectorized daily simulation.

### Execution Assumption

The strategy enters positions at today's close and realizes the return at the next day's close:

```python
daily_returns = close_px.pct_change().shift(-1)
port_returns  = (w_wide * daily_returns).sum(axis=1)
```

This is a simplification. In practice, execution at close is difficult without MOC orders.

### Transaction Costs

Costs are applied as a fraction of portfolio weight turnover per day:

```python
turnover  = w_wide.diff().abs().sum(axis=1)
tc_drag   = turnover * (TRANSACTION_COST_BPS / 10_000)
net_returns = port_returns - tc_drag
```

`TRANSACTION_COST_BPS = 5.0`, meaning 0.05% round-trip per unit of weight changed.
This does not model bid-ask spread or market impact separately.

### Portfolio Construction

The portfolio is long/short and market-neutral. Weights are generated in `portfolio.py`:

1. Predictions are demeaned cross-sectionally each day
2. Demeaned predictions are scaled so the sum of absolute weights equals 1.0
3. Individual positions are clipped to `[-0.15, +0.15]`
4. If gross leverage exceeds 1.0 after clipping, weights are re-normalized

### Metrics Computed

| Metric              | Description                                         |
|---------------------|-----------------------------------------------------|
| `Ann_Return`        | Compounded annualized return (252 trading days)     |
| `Ann_Vol`           | Annualized standard deviation of daily net returns  |
| `Sharpe`            | Ann_Return / Ann_Vol (no risk-free rate subtracted) |
| `Max_Drawdown`      | Peak-to-trough decline in cumulative wealth         |
| `Calmar`            | Ann_Return / abs(Max_Drawdown)                      |
| `Avg_Daily_Turnover`| Average daily sum of absolute weight changes        |

---

## Results

Results are exploratory. The pipeline produces numerical metrics but they should be
interpreted cautiously given the data limitations described below. No results are
claimed as evidence of a deployable strategy.

The pipeline does run end-to-end without errors and produces non-trivial IC scores
during tuning (positive IC on validation folds in most runs), which indicates some
signal in the features. Whether that signal would survive out-of-sample or in live
conditions is unknown.

---

## Limitations and Risks

**Data quality**
- Yahoo Finance data is generally reliable for liquid large-caps but has known gaps and
  occasional corporate action errors. No independent data validation has been done.
- Survivorship bias is present. The universe only contains stocks that survived to 2024.

**Methodology**
- The entire backtest is in-sample with respect to the feature design. Features were chosen
  after looking at what tends to work in equities literature. This is a soft form of
  look-ahead bias that is hard to eliminate in a personal research project.
- The embargo gap addresses label leakage but does not account for regime changes or
  distribution shift over the 9-year period.
- No walk-forward out-of-sample test was implemented. A proper OOS test would hold out
  the last 1–2 years entirely and never touch them during development.

**Execution realism**
- Entry at close is assumed. In practice, trading at closing price requires specific order
  types and exchange access.
- Market impact is not modeled. The strategy rebalances daily across 40 stocks, which at
  any real capital size would move prices.
- Slippage and borrow costs for short positions are not included.

**Model**
- Only LightGBM is used. No comparison against simpler baselines (e.g., equal-weight
  momentum) has been implemented.
- Feature importance and SHAP values are in `requirements.txt` (SHAP is a dependency)
  but are not currently wired into the main pipeline.

---

## How to Run

### Prerequisites

- Python 3.10+
- Node.js 18+ (for the dashboard frontend)

### Setup

```bash
# Clone the repo
git clone <repo-url>
cd "Alpha Engine Machine Learning Driven Quantitative Trading Pipeline"

# Python environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -r requirements.txt

# Dashboard frontend
cd dashboard
npm install
cd ..
```

### Run

```bash
python main.py
```

This will:
1. Fetch data from Yahoo Finance (~40 tickers, 2015–2024)
2. Engineer features and tune hyperparameters
3. Train the LightGBM model
4. Construct portfolio weights and run the backtest
5. Export results to `dashboard/public/dashboard_data.json`
6. Start the FastAPI backend on port 8000
7. Start the Vite dev server on port 5173
8. Open the dashboard in your default browser

Ctrl+C shuts down both servers cleanly.

### Modifying the Universe or Parameters

All configurable values live in `config.py`:

```python
UNIVERSE             = [...]          # List of yfinance tickers
START_DATE           = '2015-01-01'
END_DATE             = '2024-01-01'
TARGET_HORIZON_DAYS  = 5             # Forward return window
TRANSACTION_COST_BPS = 5.0
MAX_LONG_WEIGHT      = 0.15
MAX_SHORT_WEIGHT     = -0.15
CV_FOLDS             = 4
EMBARGO_PCT          = 0.02
LGBM_PARAMS          = {...}
```

---

## What This Project Demonstrates

- End-to-end quantitative pipeline design in Python
- Time-series-correct cross-validation (purged split with embargo)
- Cross-sectional feature engineering with rank normalization
- Information Coefficient as a model selection criterion
- Ensemble prediction across CV folds
- Market-neutral portfolio construction with position constraints
- Vectorized backtesting with explicit transaction cost modeling
- Full-stack result visualization (FastAPI + React)

---

## Why This Project Was Built

I wanted to understand what it actually takes to go from raw price data to a backtested
signal-driven strategy — without relying on a library that abstracts away all the
decisions that matter. Every component here (the CV splitter, the factor normalization,
the portfolio construction, the cost model) was written from scratch to force that
understanding. The project is research infrastructure, not a finished product.
