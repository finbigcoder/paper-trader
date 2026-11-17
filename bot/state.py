"""Todo lo que el bot recuerda vive en la carpeta ``state/`` (se sube al repo en cada
corrida). El dashboard solo lee de ahí."""
from __future__ import annotations

import json
import math
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd


def load_json(path: Path, default):
    path = Path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def finite(obj):
    """NaN e infinitos → None: Python los escribe en el JSON, pero el navegador no puede leerlos."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: finite(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [finite(v) for v in obj]
    return obj


def save_json(path: Path, obj) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(finite(obj), indent=1, ensure_ascii=False, default=str), encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_snapshot(sd: Path, broker, when: str | None = None) -> dict:
    """Foto de la cuenta: saldo, posiciones, órdenes recientes e historia de equity."""
    snap = {"updated_at": when or now_iso(), "broker": broker.name,
            "account": broker.account(), "positions": broker.positions()}
    for key, fn in (("orders", broker.recent_orders), ("equity_history", broker.equity_history)):
        try:
            snap[key] = fn()
        except Exception as exc:
            snap[key] = []
            snap.setdefault("errors", []).append(f"{key}: {type(exc).__name__}: {exc}"[:200])
    save_json(sd / "snapshot.json", snap)
    return snap


def write_benchmark(sd: Path, prices: pd.DataFrame, symbol: str, days: int = 260) -> None:
    b = prices[prices["symbol"] == symbol].sort_values("date").tail(days)
    save_json(sd / "benchmark.json", {"symbol": symbol, "series": [
        {"date": d.strftime("%Y-%m-%d"), "close": float(c)} for d, c in zip(b["date"], b["close"])]})

