"""Después del cierre: foto de la cuenta y bitácora del día. Sin LLM, costo $0.

    python -m bot.snapshot
"""
from __future__ import annotations

import os
import sys
from datetime import timedelta

from .config import ny_today, state_dir
from .journal import record_fills, update_journal
from .state import load_json, save_json, write_snapshot


def main() -> int:
    if not (os.environ.get("ALPACA_API_KEY") and os.environ.get("ALPACA_SECRET_KEY")):
        print("[bot] faltan las llaves de Alpaca; no se tomó la foto.")
        return 0
    from .broker import AlpacaPaperBroker

    sd, today, broker = state_dir(), ny_today(), AlpacaPaperBroker()
    snap = write_snapshot(sd, broker)
    new = record_fills(sd, broker.fills_since(today - timedelta(days=5)))
    trades = update_journal(sd)
    status = load_json(sd / "status.json", {})
    status["snapshot_at"] = snap["updated_at"]
    save_json(sd / "status.json", status)
    print(f"[bot] foto guardada: equity ${snap['account']['equity']:,.2f}, {len(snap['positions'])} posiciones, "
          f"{new} ejecuciones nuevas, {len(trades)} operaciones cerradas en la bitácora")
    return 0


if __name__ == "__main__":
    sys.exit(main())
