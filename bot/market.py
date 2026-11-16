"""Lo que el agente ve del mercado.

* ``prepare_day``  una vez al día (primer despertar): OpenBB baja el histórico y el
                   calendario de resultados, Qlib calcula el momentum, y se guarda un
                   resumen por acción. También lleva la regla de referencia (top-10 de
                   momentum) con la que se compara al agente.
* ``Intraday``     en cada despertar: precio de hoy (incluido pre y post-market) vía
                   Yahoo Finance. Alpaca solo da gratis datos de IEX, que casi no cubren
                   fuera del horario regular.
"""
from __future__ import annotations

import warnings
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .config import NY, weekdays_between
from .data import fetch_earnings, fetch_prices, last_closes
from .qlib_signals import rank_universe
from .state import load_json, save_json


def symbol_stats(prices: pd.DataFrame, ranking: list[dict]) -> dict[str, dict]:
    """Resumen diario por símbolo con datos al último cierre."""
    rank = {r["symbol"]: r for r in ranking}
    out = {}
    for sym, g in prices.sort_values("date").groupby("symbol"):
        if len(g) < 25:
            continue
        c, h, l, v = g["close"].to_numpy(), g["high"].to_numpy(), g["low"].to_numpy(), g["volume"].to_numpy()
        prev = np.r_[c[0], c[:-1]]
        tr = np.maximum.reduce([h - l, abs(h - prev), abs(l - prev)])
        atr = float(pd.Series(tr).rolling(14).mean().iloc[-1])
        ret = lambda n: round(float(c[-1] / c[-1 - n] - 1), 4) if len(c) > n else None  # noqa: E731
        out[sym] = {
            "close": round(float(c[-1]), 4), "ret_1d": ret(1), "ret_5d": ret(5), "ret_21d": ret(21), "ret_63d": ret(63),
            "atr_pct": round(atr / float(c[-1]), 4) if atr == atr else None,
            "vs_sma20": round(float(c[-1] / c[-20:].mean() - 1), 4),
            "vs_sma50": round(float(c[-1] / c[-50:].mean() - 1), 4) if len(c) >= 50 else None,
            "volume_ratio": round(float(v[-1] / v[-21:-1].mean()), 2) if v[-21:-1].mean() else None,
            "momentum_12_1": round(rank[sym]["score"], 4) if sym in rank else None,
            "momentum_rank": rank[sym]["rank"] if sym in rank else None,
        }
    return out


def prepare_day(cfg: dict, sd: Path, today: date, workdir: Path, held: list[str], use_qlib: bool = True,
                prices: pd.DataFrame | None = None, data_meta: dict | None = None,
                earnings: tuple[list[dict], dict] | None = None) -> tuple[dict, pd.DataFrame]:
    """Devuelve (resumen del día, precios diarios). Los argumentos opcionales los usa la
    demo para no volver a descargar."""
    if earnings is None:
        earnings = fetch_earnings(today, float(cfg["candidates"]["earnings_min_market_cap"]))
    ern, ern_meta = earnings
    if prices is None:
        symbols = cfg["universe"] + [cfg["benchmark"]] + held + [e["symbol"] for e in ern[: int(cfg["candidates"]["earnings"])]]
        prices, data_meta = fetch_prices(symbols, cfg["data"]["history_start"], cfg["data"]["providers"], today)
    signals = rank_universe(prices, cfg["universe"], workdir, use_qlib)
    stats = symbol_stats(prices, signals["ranking"])

    # Regla de referencia: top-N de momentum, rearmada cada K días hábiles. No se opera.
    book = load_json(sd / "book.json", {})
    br = cfg["benchmark_rule"]
    since = book.get("rule_since")
    if since is None or weekdays_between(date.fromisoformat(since), today) >= int(br["rebalance_days"]):
        book["rule_core"] = [r["symbol"] for r in signals["ranking"] if r["symbol"] in stats][: int(br["top_n"])]
        book["rule_since"] = today.isoformat()
        save_json(sd / "book.json", book)

    warnings_out = []
    for m in ((data_meta or {}).get("cleaning") or {}).get("suspicious_moves", []):
        warnings_out.append(f"{m['symbol']} movió {m['ret']:+.0%} el {m['date']} con volumen normal: probable escisión o error del proveedor")
    if not ern_meta.get("ok", True):
        warnings_out.append(f"el calendario de resultados no respondió: {ern_meta.get('error')}")
    prep = {
        "date": today.isoformat(), "data": {**(data_meta or {}), "earnings": ern_meta},
        "signals": {k: v for k, v in signals.items() if k != "ranking"},
        "ranking": signals["ranking"][:40],
        "earnings": [e for e in ern if e["symbol"] in stats][: int(cfg["candidates"]["earnings"])],
        "stats": stats, "rule_core": book["rule_core"], "rule_since": book["rule_since"], "warnings": warnings_out,
    }
    return prep, prices


class Intraday:
    """Precios de hoy con pre y post-market (Yahoo Finance, barras de 5 minutos)."""

    def __init__(self, prev_close: dict[str, float]):
        self.prev_close = prev_close
        self.bars: dict[str, pd.DataFrame] = {}

    def load(self, symbols: list[str]) -> None:
        import yfinance as yf

        symbols = sorted({s for s in symbols if s})
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            raw = yf.download(symbols, period="2d", interval="5m", prepost=True, progress=False, group_by="ticker", threads=True)
        today = datetime.now(NY).date()
        for s in symbols:
            try:
                df = (raw[s] if len(symbols) > 1 else raw).dropna(how="all")
            except KeyError:
                continue
            if df.empty:
                continue
            df.index = df.index.tz_convert(NY)
            self.bars[s] = df[df.index.date == today]

    def quote(self, sym: str) -> dict | None:
        df = self.bars.get(sym)
        pc = self.prev_close.get(sym)
        if df is None or df.empty or not pc:
            return {"last": pc, "chg": 0.0, "as_of": None} if pc else None
        last = float(df["Close"].dropna().iloc[-1])
        return {"last": round(last, 2), "chg": round(last / pc - 1, 4), "high": round(float(df["High"].max()), 2),
                "low": round(float(df["Low"].min()), 2), "volume": int(df["Volume"].sum()),
                "as_of": df.index[-1].strftime("%H:%M")}

    def summary(self, sym: str, every: str = "30min") -> list[str]:
        df = self.bars.get(sym)
        if df is None or df.empty:
            return []
        r = df.resample(every).agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna()
        return [f"{i:%H:%M} O{o:.2f} H{h:.2f} L{lo:.2f} C{c:.2f} V{int(v)}" for i, (o, h, lo, c, v) in r.iterrows()]


class StaticIntraday(Intraday):
    """Para la demo y los tests: precios fijos que el simulador va moviendo."""

    def __init__(self, prev_close: dict[str, float], now: dict[str, float]):
        super().__init__(prev_close)
        self.now = now

    def load(self, symbols: list[str]) -> None:
        pass

    def quote(self, sym: str) -> dict | None:
        pc, last = self.prev_close.get(sym), self.now.get(sym)
        if not last:
            return {"last": pc, "chg": 0.0, "as_of": None} if pc else None
        return {"last": round(last, 2), "chg": round(last / pc - 1, 4) if pc else 0.0, "as_of": "sim"}

    def summary(self, sym: str, every: str = "30min") -> list[str]:
        q = self.quote(sym)
        return [f"último {q['last']}"] if q else []


def prev_closes(prices: pd.DataFrame) -> dict[str, float]:
    return last_closes(prices)
