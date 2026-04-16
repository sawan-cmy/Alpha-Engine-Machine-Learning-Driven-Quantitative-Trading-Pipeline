# Alpha Engine — ML-Driven Quantitative Trading Research Pipeline

A Python research pipeline for systematically generating, evaluating, and backtesting
machine-learning-based trading signals on Indian equities (Nifty 50).
Not a live trading system. Built for research and experimentation.

---

## What It Does

- Pulls OHLCV data for ~40 Nifty 50 stocks from Yahoo Finance (2015–2024)
- Engineers cross-sectional factors: momentum, mean reversion, volatility, volume shock
- Trains a LightGBM model using purged, embargoed time-series cross-validation
- Constructs a market-neutral long/short portfolio from model predictions
- Backtests with transaction cost drag and reports Sharpe, drawdown, Calmar, and turnover
- Exports results to a React + FastAPI dashboard served locally

---

## Pipeline (High Level)

```
Raw OHLCV Data
      |
      v
 Feature Engineering  --  7 cross-sectional factors, rank-normalized per day
      |
      v
 Hyperparameter Tuning  --  Grid search scored by Information Coefficient (IC)
      |
      v
 LightGBM Model  --  Purged k-fold CV, ensemble prediction averaged across folds
      |
      v
 Portfolio Construction  --  Demeaned signal, position limits ±15%, gross leverage ≤ 1.0
      |
      v
 Vectorized Backtest  --  Daily returns, 5 bps transaction cost, cumulative metrics
      |
      v
 Dashboard  --  FastAPI backend + Vite/React frontend at localhost:5173
```

---

## Models / Methods

- **LightGBM** (regression on 5-day forward returns)
- Purged time-series cross-validation with 2% embargo gap
- Grid-search tuning over depth, leaves, learning rate — selected by mean daily IC
- Ensemble: predictions averaged across all CV fold models

---

## Backtesting & Evaluation

Vectorized daily P&L simulation. Reports annualized return, volatility, Sharpe, max drawdown, Calmar ratio, and average daily turnover. Transaction costs deducted at 5 bps per unit of weight turnover.

---

## Key Limitations

- Data sourced from Yahoo Finance — survivorship bias is present (no delisted stocks)
- Single model class (LightGBM); no blending with other model families
- Backtest does not account for slippage, market impact, or execution latency

---

## How to Run

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cd dashboard && npm install && cd ..
python main.py
```

Dashboard opens automatically at `http://localhost:5173`.

---

**Why this project exists:** To build hands-on intuition for the full quant research loop — from raw price data to a backtested, signal-driven strategy — without abstracting away what matters.
