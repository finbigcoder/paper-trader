"""Bitácora y atribución: la parte que permite saber si algo del bot aporta.

  * ``record_fills``     guarda cada ejecución una sola vez en state/fills.json
  * ``round_trips``      arma operaciones de varios días (compra → venta) por FIFO
  * ``update_virtual``   lleva día a día la regla de referencia (top-10 de momentum, sin IA) y
                         SPY: contra ellas se mide al agente
  * ``backfill_research`` cuando pasan N días, anota qué hizo cada acción investigada contra
                         SPY; así se ve si un Buy de TradingAgents le gana a un Sell
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from .state import load_json, save_json


def record_fills(sd: Path, fills: list[dict]) -> int:
    path = sd / "fills.json"
    have = load_json(path, [])
    keys = {(f.get("id"), f["at"], f["symbol"], f["qty"]) for f in have}
    new = [f for f in fills if (f.get("id"), f["at"], f["symbol"], f["qty"]) not in keys]
    if new:
        save_json(path, sorted(have + new, key=lambda f: f["at"]))
    return len(new)


def round_trips(fills: list[dict]) -> tuple[list[dict], dict[str, list[dict]]]:
    """FIFO por símbolo. Devuelve (operaciones cerradas, lotes abiertos por símbolo)."""
    lots: dict[str, list[dict]] = {}
    closed: list[dict] = []
    for f in sorted(fills, key=lambda x: x["at"]):
        sym, q = f["symbol"], float(f["qty"]) * (1 if f["side"] == "buy" else -1)
        book = lots.setdefault(sym, [])
        while q and book and (book[0]["qty"] > 0) != (q > 0):
            lot = book[0]
            take = min(abs(q), abs(lot["qty"]))
            sign = 1 if lot["qty"] > 0 else -1
            closed.append({"symbol": sym, "side": "long" if sign > 0 else "short", "qty": take,
                           "entry_date": lot["at"][:10], "entry": round(lot["price"], 4),
                           "exit_date": f["at"][:10], "exit": round(float(f["price"]), 4),
                           "pnl_usd": round(sign * take * (float(f["price"]) - lot["price"]), 2),
                           "ret": round(sign * (float(f["price"]) / lot["price"] - 1), 5)})
            lot["qty"] -= sign * take
            q += sign * take
            if abs(lot["qty"]) < 1e-9:
                book.pop(0)
        if abs(q) > 1e-9:
            book.append({"qty": q, "price": float(f["price"]), "at": f["at"]})
    for t in closed:
        t["days"] = int(len(pd.bdate_range(t["entry_date"], t["exit_date"])) - 1)
    return closed, {s: b for s, b in lots.items() if b}


def update_journal(sd: Path) -> list[dict]:
    trades, _ = round_trips(load_json(sd / "fills.json", []))
    save_json(sd / "journal.json", trades)
    return trades


def update_virtual(sd: Path, prices: pd.DataFrame, benchmark: str) -> int:
    """Serie diaria de la regla de referencia (top-N de momentum a pesos iguales, sin IA)
    y de SPY desde el primer día del agente. Se recalcula completa cada mañana."""
    days = sorted((load_json(p, {}) for p in (sd / "days").glob("*.json")), key=lambda d: d.get("date", ""))
    cores = [(pd.Timestamp(d["date"]), d["prep"]["rule_core"]) for d in days if (d.get("prep") or {}).get("rule_core")]
    if not cores:
        return 0
    c = prices.pivot(index="date", columns="symbol", values="close").sort_index()
    r = c.pct_change(fill_method=None)
    rows = []
    for d in r.index[r.index >= cores[0][0]]:
        core = [names for when, names in cores if when <= d][-1]
        cols = [x for x in core if x in r.columns]
        cr = r.loc[d, cols].mean() if cols else None
        sr = r.loc[d, benchmark] if benchmark in r.columns else None
        if cr is not None and cr == cr and sr is not None and sr == sr:
            rows.append({"date": d.strftime("%Y-%m-%d"), "core_ret": round(float(cr), 6), "spy_ret": round(float(sr), 6)})
    save_json(sd / "virtual.json", rows)
    return len(rows)


def backfill_research(sd: Path, prices: pd.DataFrame, benchmark: str, horizon: int) -> int:
    """Para cada investigación con ``horizon`` sesiones de historia posterior: retorno de la
    acción y de SPY desde el cierre previo a la investigación."""
    path = sd / "research.json"
    hist = load_json(path, [])
    c = prices.pivot(index="date", columns="symbol", values="close").sort_index()
    dates, done = c.index, 0
    for e in hist:
        if "fwd_ret" in e or e["symbol"] not in c.columns or benchmark not in c.columns:
            continue
        before = dates[dates < pd.Timestamp(e["date"])]
        if not len(before):
            continue
        i0 = dates.get_loc(before[-1])
        if i0 + horizon >= len(dates) or not c[e["symbol"]].iloc[i0] > 0:
            continue
        i1 = i0 + horizon
        e["fwd_ret"] = round(float(c[e["symbol"]].iloc[i1] / c[e["symbol"]].iloc[i0] - 1), 5)
        e["fwd_spy"] = round(float(c[benchmark].iloc[i1] / c[benchmark].iloc[i0] - 1), 5)
        e["fwd_days"] = horizon
        done += 1
    if done:
        save_json(path, hist)
    return done
