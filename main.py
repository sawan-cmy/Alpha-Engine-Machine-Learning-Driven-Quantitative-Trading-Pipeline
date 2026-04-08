import sys
import time
import signal
import socket
import logging
import subprocess
import webbrowser
from pathlib import Path

import config
from data_loader import DataLoader
from factors import FactorEngineer
from tuner import HyperparameterTuner
from model import LightGBMModel
from portfolio import PortfolioConstructor
from backtest import Backtester
from visualization import generate_tearsheet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent
DASHBOARD   = ROOT / "dashboard"
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"

BACKEND_PORT  = 8000
FRONTEND_PORT = 5173


# ── Helpers ────────────────────────────────────────────────────────────────────

def _wait_for_port(port: int, timeout: int = 40) -> bool:
    """Poll until the port is accepting TCP connections (or timeout)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def _kill(proc: subprocess.Popen) -> None:
    """Kill the process tree — on Windows uses taskkill /T to also kill npm children."""
    try:
        if sys.platform == "win32":
            subprocess.call(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            proc.terminate()
            proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


# ── Process launchers ──────────────────────────────────────────────────────────

def _start_backend() -> subprocess.Popen:
    """
    Launch FastAPI + uvicorn as a background process.
    Uses shell=True so Windows cmd.exe resolves the venv Python path correctly.
    """
    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    cmd = (
        f'"{python}" -m uvicorn backend.server:app '
        f'--host 0.0.0.0 --port {BACKEND_PORT}'
    )
    logging.info(f"[launcher] Starting backend on port {BACKEND_PORT}")
    return subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        shell=True,            # ← shell=True is required on Windows
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _start_frontend() -> subprocess.Popen:
    """
    Launch Vite dev server as a background process.
    Uses shell=True so Windows cmd.exe can find npm.cmd in PATH.
    """
    logging.info(f"[launcher] Starting frontend on port {FRONTEND_PORT}")
    return subprocess.Popen(
        "npm run dev",
        cwd=str(DASHBOARD),
        shell=True,            # ← shell=True is required on Windows to find npm.cmd
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


# ── Orchestrator ───────────────────────────────────────────────────────────────

def _launch_dashboard() -> None:
    """
    1. Start FastAPI backend  (port 8000)
    2. Start Vite frontend    (port 5173)
    3. Wait for both to be ready
    4. Open http://localhost:5173 in the default browser
    5. Block until Ctrl+C, then clean up both processes
    """
    backend_proc  = _start_backend()
    frontend_proc = _start_frontend()
    procs = [backend_proc, frontend_proc]

    def _cleanup(signum=None, frame=None):
        logging.info("[launcher] Stopping dashboard servers…")
        for p in procs:
            _kill(p)

    signal.signal(signal.SIGTERM, _cleanup)
    # SIGINT only on POSIX; on Windows KeyboardInterrupt is caught in main()
    if sys.platform != "win32":
        signal.signal(signal.SIGINT, _cleanup)

    # ── Wait for backend ──
    logging.info("[launcher] Waiting for backend  (port 8000)…")
    if _wait_for_port(BACKEND_PORT, timeout=30):
        logging.info("[launcher] ✓ Backend ready")
    else:
        logging.warning("[launcher] Backend took too long — dashboard may show stale data")

    # ── Wait for frontend ──
    logging.info("[launcher] Waiting for frontend (port 5173)…")
    if _wait_for_port(FRONTEND_PORT, timeout=45):
        logging.info("[launcher] ✓ Frontend ready — opening browser")
        webbrowser.open(f"http://localhost:{FRONTEND_PORT}")
    else:
        logging.warning(
            "[launcher] Frontend not ready — open http://localhost:5173 manually"
        )

    logging.info("=" * 60)
    logging.info("  Dashboard live at http://localhost:5173")
    logging.info("  Press Ctrl+C to stop.")
    logging.info("=" * 60)

    # ── Keep alive until Ctrl+C ──
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("\n[launcher] Ctrl+C — shutting down…")
        _cleanup()


# ── Main pipeline ──────────────────────────────────────────────────────────────

def main():
    logging.info("=" * 60)
    logging.info("  QUANTITATIVE PIPELINE START")
    logging.info("=" * 60)

    # 1. Load Data
    loader    = DataLoader(config.UNIVERSE, config.START_DATE, config.END_DATE)
    df_prices = loader.fetch_data()

    # 2. Build Factors
    engineer = FactorEngineer(config)
    factors_df, feature_cols = engineer.build_factors(df_prices)

    X = factors_df[feature_cols]
    y = factors_df["target"]

    # 2.5 Tune Hyperparameters
    tuner       = HyperparameterTuner(config)
    best_params = tuner.tune(X, y)
    config.LGBM_PARAMS.update(best_params)

    # 3. Train Model & Predict
    lgb_model = LightGBMModel(config)
    lgb_model.fit(X, y)
    factors_df["prediction"] = lgb_model.predict(X)

    # 4. Generate Signal / Weights
    portfolio = PortfolioConstructor(config)
    weights   = portfolio.generate_weights(factors_df)

    # 5. Backtest
    backtester = Backtester(config)
    metrics, cum_returns, net_returns = backtester.run(df_prices, weights)

    logging.info("--- BACKTEST RESULTS ---")
    for k, v in metrics.items():
        if any(x in k for x in ["Turnover", "Sharpe", "Calmar"]):
            logging.info(f"  {k}: {v:.4f}")
        else:
            logging.info(f"  {k}: {v:.2%}")

    # 6. Export JSON (feeds React UI) + write HTML tearsheet
    generate_tearsheet(cum_returns, net_returns, metrics)
    logging.info("✓ Dashboard data exported to dashboard/public/dashboard_data.json")

    # 7. Launch servers and open browser
    _launch_dashboard()


if __name__ == "__main__":
    main()
