from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parent.parent
NY = ZoneInfo("America/New_York")


def load_config(path: str | Path | None = None) -> dict:
    path = Path(path or os.environ.get("BOT_CONFIG") or ROOT / "config.yaml")
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    if cfg.get("mode") not in ("paper", "dry_run"):
        raise ValueError("config.mode debe ser 'paper' o 'dry_run'")
    if float(cfg["budget"]["monthly_usd"]) < 0:
        raise ValueError("budget.monthly_usd no puede ser negativo")
    cfg["universe"] = [s.upper() for s in cfg["universe"]]
    cfg["benchmark"] = cfg["benchmark"].upper()
    return cfg


def state_dir(override: str | Path | None = None) -> Path:
    d = Path(override or os.environ.get("BOT_STATE_DIR") or ROOT / "state")
    d.mkdir(parents=True, exist_ok=True)
    return d


def ny_today() -> date:
    return datetime.now(NY).date()


def weekdays_left_in_month(d: date) -> int:
    """Días hábiles (lun-vie) desde ``d`` hasta fin de mes, contando ``d``. Ignora feriados."""
    n, cur = 0, d
    while cur.month == d.month:
        if cur.weekday() < 5:
            n += 1
        cur += timedelta(days=1)
    return max(n, 1)


def previous_weekday(d: date) -> date:
    cur = d - timedelta(days=1)
    while cur.weekday() >= 5:
        cur -= timedelta(days=1)
    return cur


def weekdays_between(a: date, b: date) -> int:
    """Días hábiles transcurridos de ``a`` a ``b`` (sin contar ``a``)."""
    n, cur = 0, a
    while cur < b:
        cur += timedelta(days=1)
        if cur.weekday() < 5:
            n += 1
    return n
