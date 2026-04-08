"""
OpenBB data service — Python 3.14 compatible.

Data priority:
  1) openbb_yfinance fetcher (OpenBB's own fetcher class, bypasses broken router)
  2) yfinance direct (always available)
  3) empty placeholders

Why bypass obb.equity?
  openbb-core 1.6.7 + openbb-equity 1.6.0 have a static-package API mismatch
  under Python 3.14 that causes ImportError in the generated equity.py router.
  The openbb_yfinance fetcher class works perfectly and is the same underlying
  code that obb.equity.price.quote() would call internally.
"""
from __future__ import annotations

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# ── Detect available backends ──────────────────────────────────────────────────
_OPENBB_YF_OK = False  # openbb_yfinance fetcher (OpenBB's own class)
_YF_OK        = False  # yfinance direct fallback

try:
    from openbb_yfinance.models.equity_quote import YFinanceEquityQuoteFetcher  # type: ignore
    from openbb_yfinance.models.equity_historical import YFinanceEquityHistoricalFetcher  # type: ignore
    _OPENBB_YF_OK = True
    logger.info("[service] ✓ OpenBB yfinance fetcher available")
except Exception as _e:
    logger.info(f"[service] OpenBB yfinance fetcher not available: {_e}")

try:
    import yfinance as yf  # type: ignore
    _YF_OK = True
    logger.info("[service] ✓ yfinance direct available")
except Exception as _e:
    logger.warning(f"[service] yfinance not found: {_e}")


# ── NSE Indian Equity Watchlist ────────────────────────────────────────────────
DEFAULT_SYMBOLS: list[str] = [
    "^NSEI",
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "HINDUNILVR.NS",
    "BHARTIARTL.NS",
    "ITC.NS",
    "SBIN.NS",
]

DISPLAY_NAMES: dict[str, str] = {
    "^NSEI":          "NIFTY 50",
    "RELIANCE.NS":    "RELIANCE",
    "TCS.NS":         "TCS",
    "INFY.NS":        "INFY",
    "HDFCBANK.NS":    "HDFC BANK",
    "ICICIBANK.NS":   "ICICI BANK",
    "HINDUNILVR.NS":  "HUL",
    "BHARTIARTL.NS":  "AIRTEL",
    "ITC.NS":         "ITC",
    "SBIN.NS":        "SBIN",
}

SECTORS: dict[str, str] = {
    "^NSEI":          "Index",
    "RELIANCE.NS":    "Energy",
    "TCS.NS":         "Technology",
    "INFY.NS":        "Technology",
    "HDFCBANK.NS":    "Financials",
    "ICICIBANK.NS":   "Financials",
    "HINDUNILVR.NS":  "Consumer",
    "BHARTIARTL.NS":  "Telecom",
    "ITC.NS":         "Consumer",
    "SBIN.NS":        "Financials",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _rnd(v: Any, n: int = 2) -> Any:
    try:
        return round(float(v), n) if v is not None else None
    except (TypeError, ValueError):
        return None


def _empty_quote(symbol: str) -> dict[str, Any]:
    return {
        "symbol":     symbol,
        "display":    DISPLAY_NAMES.get(symbol, symbol),
        "sector":     SECTORS.get(symbol, ""),
        "price":      None,
        "change":     None,
        "change_pct": None,
        "volume":     None,
        "high":       None,
        "low":        None,
        "open":       None,
        "prev_close": None,
        "market_cap": None,
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "source":     "OpenBB",
    }


# ── OpenBB yfinance fetcher (uses OpenBB's own model classes) ─────────────────

async def _fetch_openbb_yfinance(symbols: list[str]) -> dict[str, dict[str, Any]]:
    """
    Await openbb_yfinance.YFinanceEquityQuoteFetcher.fetch_data() — it's async.
    This is what obb.equity.price.quote(provider='yfinance') calls internally.
    """
    results: dict[str, dict[str, Any]] = {}
    try:
        fetcher = YFinanceEquityQuoteFetcher()
        raw = await fetcher.fetch_data(
            params={"symbol": ",".join(symbols)},
            credentials={},
        )
        rows = list(raw) if raw else []
        for row in rows:
            sym = getattr(row, "symbol", None)
            if not sym:
                # Try matching by position if symbol missing
                continue

            price      = _rnd(getattr(row, "last_price",  None))
            prev_close = _rnd(getattr(row, "prev_close",  None))
            change     = _rnd((price - prev_close) if price and prev_close else None)
            change_pct = _rnd((change / prev_close * 100) if change and prev_close else None)

            results[sym] = {
                "symbol":     sym,
                "display":    DISPLAY_NAMES.get(sym, sym),
                "sector":     SECTORS.get(sym, ""),
                "price":      price,
                "change":     change,
                "change_pct": change_pct,
                "volume":     getattr(row, "volume",     None),
                "high":       _rnd(getattr(row, "high",  None)),
                "low":        _rnd(getattr(row, "low",   None)),
                "open":       _rnd(getattr(row, "open",  None)),
                "prev_close": prev_close,
                "market_cap": getattr(row, "market_cap", None),
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "source":     "OpenBB (yfinance)",
            }
    except Exception as exc:
        logger.error(f"[openbb_yfinance] batch fetch error: {exc}")

    # Fill in any symbols not returned
    for sym in symbols:
        results.setdefault(sym, _empty_quote(sym))
    return results


# ── yfinance direct fallback ───────────────────────────────────────────────────

def _fetch_yfinance_quotes(symbols: list[str]) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    try:
        raw = yf.Tickers(" ".join(symbols))
        for sym in symbols:
            try:
                tk = raw.tickers.get(sym) or yf.Ticker(sym)
                fi = tk.fast_info
                price      = _rnd(getattr(fi, "last_price",       None))
                prev_close = _rnd(getattr(fi, "previous_close",   None))
                change     = _rnd((price - prev_close) if price and prev_close else None)
                change_pct = _rnd((change / prev_close * 100) if change and prev_close else None)

                results[sym] = {
                    "symbol":     sym,
                    "display":    DISPLAY_NAMES.get(sym, sym),
                    "sector":     SECTORS.get(sym, ""),
                    "price":      price,
                    "change":     change,
                    "change_pct": change_pct,
                    "volume":     getattr(fi, "three_month_average_volume", None),
                    "high":       _rnd(getattr(fi, "day_high",  None)),
                    "low":        _rnd(getattr(fi, "day_low",   None)),
                    "open":       _rnd(getattr(fi, "open",      None)),
                    "prev_close": prev_close,
                    "market_cap": getattr(fi, "market_cap",     None),
                    "updated_at": datetime.utcnow().isoformat() + "Z",
                    "source":     "OpenBB (yfinance)",
                }
            except Exception as exc:
                logger.debug(f"[yfinance] {sym}: {exc}")
                results[sym] = _empty_quote(sym)
    except Exception as exc:
        logger.error(f"[yfinance] batch fetch failed: {exc}")
        for sym in symbols:
            results[sym] = _empty_quote(sym)
    return results


# ── OHLCV history ──────────────────────────────────────────────────────────────

async def _fetch_history_openbb_yf(symbol: str, days: int) -> list[dict]:
    start = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        fetcher = YFinanceEquityHistoricalFetcher()
        raw = await fetcher.fetch_data(
            params={"symbol": symbol, "start_date": start},
            credentials={},
        )
        records = []
        for row in (list(raw) if raw else []):
            d = getattr(row, "date", None)
            c = getattr(row, "close", None)
            if d is None or c is None:
                continue
            records.append({
                "date":   d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)[:10],
                "open":   _rnd(getattr(row, "open",   None)),
                "high":   _rnd(getattr(row, "high",   None)),
                "low":    _rnd(getattr(row, "low",    None)),
                "close":  _rnd(c),
                "volume": getattr(row, "volume", None),
            })
        return records
    except Exception as exc:
        logger.warning(f"[openbb_yfinance] history {symbol}: {exc}")
        return []


def _fetch_history_yf(symbol: str, days: int) -> list[dict]:
    end   = datetime.utcnow()
    start = end - timedelta(days=days)
    try:
        df = yf.download(
            symbol, start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"), progress=False, auto_adjust=True,
        )
        if df.empty:
            return []
        df = df.reset_index()
        df.columns = [
            c[0].lower() if isinstance(c, tuple) else str(c).lower()
            for c in df.columns
        ]
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        keep = ["date", "open", "high", "low", "close", "volume"]
        df = df[[c for c in keep if c in df.columns]]
        return df.dropna(subset=["close"]).to_dict(orient="records")
    except Exception as exc:
        logger.error(f"[yfinance] history {symbol}: {exc}")
        return []


# ── Public async API ───────────────────────────────────────────────────────────

async def get_live_quotes(symbols: list[str] | None = None) -> dict[str, dict]:
    syms = symbols or DEFAULT_SYMBOLS

    if _OPENBB_YF_OK:
        try:
            return await _fetch_openbb_yfinance(syms)
        except Exception as exc:
            logger.warning(f"[service] OpenBB fetcher failed, falling back: {exc}")

    if _YF_OK:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch_yfinance_quotes, syms)

    return {s: _empty_quote(s) for s in syms}


async def get_historical(symbol: str, days: int = 365) -> list[dict]:
    if _OPENBB_YF_OK:
        try:
            data = await _fetch_history_openbb_yf(symbol, days)
            if data:
                return data
        except Exception as exc:
            logger.warning(f"[service] OpenBB history failed, falling back: {exc}")

    if _YF_OK:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch_history_yf, symbol, days)

    return []
