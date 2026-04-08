"""
Production FastAPI WebSocket server for the Quant Fund Dashboard.

Endpoints:
  WS  /ws                       — live broadcast every 30s
  GET /api/symbols               — watchlist
  GET /api/quotes                — latest snapshot
  GET /api/history/{symbol}      — OHLCV history (365 days)
  GET /api/metrics               — strategy metrics from dashboard_data.json
  GET /health                    — health-check

Run:
  uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.openbb_service import (
    DEFAULT_SYMBOLS, DISPLAY_NAMES, get_live_quotes, get_historical
)

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
POLL_INTERVAL: int = int(os.getenv("POLL_INTERVAL_SECS", "30"))
DASHBOARD_JSON: Path = Path(__file__).parent.parent / "dashboard" / "public" / "dashboard_data.json"

# ── In-memory state ────────────────────────────────────────────────────────────
_latest_quotes: dict[str, Any] = {}
_history_cache: dict[str, list[dict]] = {}


# ── Connection Manager ─────────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)
        logger.info(f"[ws] client connected — total: {len(self.active)}")

    def disconnect(self, ws: WebSocket) -> None:
        self.active.remove(ws)
        logger.info(f"[ws] client disconnected — total: {len(self.active)}")

    async def broadcast(self, payload: dict) -> None:
        dead: list[WebSocket] = []
        for ws in self.active:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)


manager = ConnectionManager()


# ── Background polling task ────────────────────────────────────────────────────

async def _poller() -> None:
    """Polls OpenBB every POLL_INTERVAL seconds, broadcasts to all WS clients."""
    logger.info(f"[poller] starting — interval={POLL_INTERVAL}s, symbols={DEFAULT_SYMBOLS}")
    while True:
        try:
            quotes = await get_live_quotes(DEFAULT_SYMBOLS)
            _latest_quotes.update(quotes)
            payload = {
                "type":      "quote_update",
                "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
                "data":      quotes,
            }
            await manager.broadcast(payload)
            logger.info(f"[poller] broadcast to {len(manager.active)} client(s)")
        except Exception as exc:
            logger.error(f"[poller] error: {exc}")
        await asyncio.sleep(POLL_INTERVAL)


# ── Lifespan ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_poller())
    logger.info("[server] startup complete")
    yield
    task.cancel()
    logger.info("[server] shutdown")


# ── FastAPI app ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Quant Fund Dashboard API",
    version="2.0.0",
    description="Real-time market data via OpenBB Platform + yfinance",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── WebSocket endpoint ─────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Send latest cached data immediately on connect
    if _latest_quotes:
        await websocket.send_json({
            "type":      "quote_update",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "data":      _latest_quotes,
        })
    try:
        while True:
            # Keep connection alive — browser sends pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ── REST endpoints ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "clients": len(manager.active)}


@app.get("/api/symbols")
async def list_symbols():
    return {
        "symbols": DEFAULT_SYMBOLS,
        "display": DISPLAY_NAMES,
    }


@app.get("/api/quotes")
async def latest_quotes():
    if not _latest_quotes:
        quotes = await get_live_quotes(DEFAULT_SYMBOLS)
        _latest_quotes.update(quotes)
    return {"data": _latest_quotes}


@app.get("/api/history/{symbol:path}")
async def history(symbol: str, days: int = 365):
    cache_key = f"{symbol}:{days}"
    if cache_key not in _history_cache:
        data = await get_historical(symbol, days)
        _history_cache[cache_key] = data
    return {"symbol": symbol, "data": _history_cache[cache_key]}


@app.get("/api/metrics")
async def metrics():
    if DASHBOARD_JSON.exists():
        try:
            with open(DASHBOARD_JSON, encoding="utf-8") as f:
                payload = json.load(f)
            return {"data": payload}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
    return {"data": None}


# ── Dev entry-point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)
