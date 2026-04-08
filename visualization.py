"""
visualization.py — Dashboard data exporter for the React TypeScript dashboard.

Exports dashboard_data.json to dashboard/public/ which the live React app reads.
The old interactive_tearsheet.html (Plotly) is no longer generated since the
TypeScript dashboard provides a superior real-time experience.
"""
import json
import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd


# ── JSON export (feeds the React / TypeScript dashboard) ──────────────────────

def _series_to_points(series: pd.Series) -> list[dict]:
    """Convert a DatetimeIndex Series to [{date, value}, …] — JSON-serialisable."""
    return [
        {"date": idx.strftime("%Y-%m-%d"), "value": round(float(val), 6)}
        for idx, val in series.items()
        if not (isinstance(val, float) and np.isnan(val))
    ]


def export_dashboard_json(
    cum_returns: pd.Series,
    net_returns: pd.Series,
    metrics: dict,
    save_dir: str | Path = "dashboard/public",
    filename: str = "dashboard_data.json",
) -> str:
    """
    Export all strategy data to dashboard_data.json consumed by the React dashboard.

    Parameters
    ----------
    cum_returns : cumulative wealth index (DatetimeIndex Series)
    net_returns : daily net returns (DatetimeIndex Series)
    metrics     : strategy performance metrics dict
    save_dir    : output directory (default: dashboard/public)
    filename    : output filename

    Returns
    -------
    str — absolute path of the written file
    """
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    # Drawdowns
    rolling_max = cum_returns.cummax()
    drawdown    = cum_returns / rolling_max - 1.0

    # Monthly returns matrix
    monthly = net_returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    monthly_records = [
        {"year": int(idx.year), "month": int(idx.month), "ret": round(float(val), 6)}
        for idx, val in monthly.items()
        if not (isinstance(val, float) and np.isnan(val))
    ]

    # Rolling 252-day Sharpe
    roll_sharpe = net_returns.rolling(252).apply(
        lambda x: x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0
    )

    payload = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "metrics": {
            "Sharpe":             round(float(metrics.get("Sharpe",             0)), 4),
            "Ann_Return":         round(float(metrics.get("Ann_Return",         0)), 4),
            "Max_Drawdown":       round(float(metrics.get("Max_Drawdown",       0)), 4),
            "Calmar":             round(float(metrics.get("Calmar",             0)), 4),
            "Ann_Volatility":     round(float(metrics.get("Ann_Vol",            0)), 4),
            "Avg_Daily_Turnover": round(float(metrics.get("Avg_Daily_Turnover", 0)), 4),
        },
        "cum_returns":     _series_to_points(cum_returns),
        "drawdowns":       _series_to_points(drawdown),
        "net_returns":     _series_to_points(net_returns),
        "monthly_returns": monthly_records,
        "roll_sharpe":     _series_to_points(roll_sharpe),
    }

    out_path = os.path.abspath(os.path.join(save_dir, filename))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))

    logging.info(f"[visualization] ✓ Dashboard JSON → {out_path}")
    return out_path


# ── Public API — called by main.py ────────────────────────────────────────────

def generate_tearsheet(
    cum_returns: pd.Series,
    net_returns: pd.Series,
    metrics: dict,
    save_path: str = "interactive_tearsheet.html",   # kept for API compatibility, ignored
    export_json: bool = True,
    json_dir: str | Path = "dashboard/public",
) -> None:
    """
    Export strategy data for the React TypeScript dashboard.

    The `save_path` / HTML argument is kept for backward-compatibility
    but the HTML file is no longer generated — the TypeScript dashboard
    at http://localhost:5173 provides a far superior real-time experience.

    Parameters
    ----------
    cum_returns : cumulative wealth index
    net_returns : daily net returns
    metrics     : strategy performance dict
    save_path   : (ignored) legacy argument – no HTML is written
    export_json : export dashboard_data.json (default True)
    json_dir    : directory for the JSON file
    """
    if export_json:
        export_dashboard_json(cum_returns, net_returns, metrics, save_dir=json_dir)
    else:
        logging.warning("[visualization] JSON export disabled — dashboard will show stale data")
