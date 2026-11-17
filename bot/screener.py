"""Pantalla de todo el mercado de EE. UU.

El LLM no puede leer miles de acciones en cada despertar (sería caro y ordenaría mal una
tabla enorme), así que el código hace el barrido y le pasa solo las mejores:

1. Candidatas: las que más suben, las que más bajan y las más activas por volumen,
   según el screener de Alpaca (mismas llaves que la cuenta paper).
2. Filtro de liquidez, con 20 días de barras diarias de Yahoo Finance: precio mínimo,
   volumen medio en dólares mínimo, símbolo operable en Alpaca.
3. Orden: tamaño del movimiento de hoy × volumen relativo (acotado). Es una heurística
   mía, no un factor probado.

Si algo falla, el despertar sigue sin pantalla y queda el aviso.
"""
from __future__ import annotations

import re
import warnings
from datetime import date

SYMBOL_RE = re.compile(r"^[A-Z]{1,5}$")       # deja fuera warrants, units y preferentes (ABC.WS, ABC-P…)


def daily_stats(symbols: list[str], today: date) -> dict[str, dict]:
    """Cierre previo y liquidez de los últimos 20 días, sin contar la barra de hoy."""
    import yfinance as yf

    if not symbols:
        return {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        raw = yf.download(sorted(symbols), period="2mo", interval="1d", auto_adjust=True, progress=False,
                          group_by="ticker", threads=True)
    out = {}
    for s in symbols:
        try:
            df = (raw[s] if len(symbols) > 1 else raw).dropna(subset=["Close"])
        except KeyError:
            continue
        past = df[[d.date() < today for d in df.index]].tail(20)
        if len(past) < 5:
            continue
        out[s] = {"prev_close": round(float(past["Close"].iloc[-1]), 4),
                  "avg_volume": float(past["Volume"].mean()),
                  "avg_dollar_volume": float((past["Close"] * past["Volume"]).mean())}
    return out


def prefilter(cands: list[dict], daily: dict[str, dict], tradable: set[str] | None, cfg: dict,
              exclude: set[str]) -> dict[str, dict]:
    """Junta las listas del screener y deja solo lo líquido y operable."""
    merged: dict[str, dict] = {}
    for c in cands:
        s = str(c.get("symbol", "")).upper()
        if not SYMBOL_RE.match(s) or s in exclude or (tradable is not None and s not in tradable):
            continue
        m = merged.setdefault(s, {"symbol": s, "sources": []})
        if c.get("source") not in m["sources"]:
            m["sources"].append(c.get("source"))
    out = {}
    for s, m in merged.items():
        d = daily.get(s)
        if not d or d["prev_close"] < float(cfg["min_price"]) or d["avg_dollar_volume"] < float(cfg["min_dollar_volume"]):
            continue
        out[s] = {**m, **d}
    return out


def rank(pre: dict[str, dict], quotes: dict[str, dict | None], size: int) -> list[dict]:
    """Ordena por |cambio de hoy| × volumen relativo (acotado entre 0.2x y 5x)."""
    rows = []
    for s, x in pre.items():
        q = quotes.get(s) or {}
        if not q.get("as_of") or q.get("chg") is None:      # sin precio de hoy no se puede evaluar
            continue
        rvol = (q.get("volume") or 0) / x["avg_volume"] if x["avg_volume"] else 0.0
        score = abs(q["chg"]) * min(max(rvol, 0.2), 5.0)
        rows.append({"symbol": s, "sources": x["sources"], "last": q.get("last"), "chg": q["chg"], "rvol": round(rvol, 2),
                     "avg_dollar_volume": round(x["avg_dollar_volume"]), "score": round(score, 5)})
    return sorted(rows, key=lambda r: -r["score"])[:size]


def candidates(cfg: dict, broker, today: date, exclude: set[str]) -> tuple[dict[str, dict], list[str]]:
    """Paso 1 y 2. Devuelve (símbolo → datos, avisos). Nunca lanza."""
    sc = cfg.get("screener") or {}
    if not sc.get("enabled") or not hasattr(broker, "screener_candidates"):
        return {}, []
    warns = []
    try:
        cands = broker.screener_candidates(int(sc.get("top", 50)))
    except Exception as exc:
        return {}, [f"screener de Alpaca falló: {type(exc).__name__}: {exc}"[:200]]
    try:
        tradable = broker.tradable_symbols()
    except Exception as exc:
        tradable = None
        warns.append(f"no se pudo leer la lista de activos operables: {type(exc).__name__}"[:200])
    syms = sorted({str(c.get("symbol", "")).upper() for c in cands} - exclude)
    syms = [s for s in syms if SYMBOL_RE.match(s) and (tradable is None or s in tradable)]
    try:
        daily = daily_stats(syms, today)
    except Exception as exc:
        return {}, warns + [f"no se pudo medir la liquidez de la pantalla: {type(exc).__name__}: {exc}"[:200]]
    return prefilter(cands, daily, tradable, sc, exclude), warns
