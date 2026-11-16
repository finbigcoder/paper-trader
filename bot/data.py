"""Etapa 1 · Datos de mercado vía OpenBB.

OpenBB es la capa de datos: una sola llamada (`obb.equity.price.historical`) trae el
histórico diario de todo el universo. El proveedor por defecto es Cboe, que no pide
API key. Si falla o viene atrasado se intenta yfinance directo como respaldo.
"""
from __future__ import annotations

import re
import time
import warnings
from datetime import date

import pandas as pd

from .config import previous_weekday

COLS = ["date", "symbol", "open", "high", "low", "close", "volume"]


def _normalize(df: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    df = df.reset_index()
    df.columns = [str(c).lower() for c in df.columns]
    if "symbol" not in df.columns:
        df["symbol"] = symbols[0]
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    df["symbol"] = df["symbol"].str.upper()
    df = df[COLS].dropna(subset=["close"])
    df = df[df["close"] > 0]
    # Cboe a veces repite la última sesión; se conserva la fila más reciente.
    return df.drop_duplicates(["symbol", "date"], keep="last")


def _from_openbb(symbols: list[str], start: str, provider: str) -> pd.DataFrame:
    """Histórico por lotes de 20. Cboe falla de forma intermitente (a veces un lote entero
    truena con un KeyError interno): cada lote se reintenta, y si sigue fallando se piden
    sus símbolos uno por uno. Lo que no llegue queda como faltante, no tumba la corrida."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from openbb import obb

    def ask(batch: list[str]) -> pd.DataFrame:
        res = obb.equity.price.historical(",".join(batch), provider=provider, start_date=start)
        return _normalize(res.to_dataframe(), batch)

    def with_retries(batch: list[str], tries: int) -> pd.DataFrame | None:
        for attempt in range(tries):
            try:
                return ask(batch)
            except Exception:
                time.sleep(1.5 * (attempt + 1))
        return None

    frames = []
    for i in range(0, len(symbols), 20):
        batch = symbols[i:i + 20]
        df = with_retries(batch, 3)
        if df is not None:
            frames.append(df)
            continue
        for sym in batch:
            one = with_retries([sym], 2)
            if one is not None:
                frames.append(one)
    if not frames:
        raise RuntimeError(f"OpenBB ({provider}) no devolvió ningún símbolo")
    out = pd.concat(frames, ignore_index=True)
    if out["symbol"].nunique() < 0.8 * len(symbols):
        raise RuntimeError(f"OpenBB ({provider}) solo devolvió {out['symbol'].nunique()} de {len(symbols)} símbolos")
    return out


def _from_yfinance(symbols: list[str], start: str) -> pd.DataFrame:
    import yfinance as yf

    raw = yf.download(symbols, start=start, auto_adjust=True, progress=False, group_by="ticker", threads=True)
    frames = []
    for sym in symbols:
        try:
            sub = raw[sym].dropna(how="all").copy()
        except KeyError:
            continue
        sub["symbol"] = sym
        frames.append(_normalize(sub.rename_axis("date"), [sym]))
    if not frames:
        raise RuntimeError("yfinance no devolvió datos")
    return pd.concat(frames, ignore_index=True)


def _meta(df: pd.DataFrame, symbols: list[str], label: str, expected: date) -> dict:
    last = df["date"].max().date()
    return {"provider": label, "last_date": last.isoformat(), "expected_last_date": expected.isoformat(),
            "stale": last < expected, "symbols_requested": len(symbols),
            "missing_symbols": sorted(set(symbols) - set(df["symbol"].unique())), "rows": int(len(df))}


def _drop_partial_dates(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Una fecha que solo trae un puñado de símbolos (sesión a medio publicar) ensucia
    el calendario de Qlib: se descarta."""
    per_day = df.groupby("date")["symbol"].nunique()
    thin = per_day[per_day < 0.5 * df["symbol"].nunique()].index
    return df[~df["date"].isin(thin)], [d.strftime("%Y-%m-%d") for d in thin]


def clean_prices(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Limpieza de errores conocidos del proveedor.

    1. Fechas duplicadas: Cboe devolvió una fila en el feriado del 26 de mayo de 2025 que
       repite la sesión anterior y, además, sin ajustar por splits (BKNG ×25, NFLX ×10).
       Se elimina toda fecha en la que al menos 80% de los símbolos repite apertura y
       cierre del día previo.
    2. Saltos sospechosos: un movimiento de más de 45% en un día con volumen menor a 2× su
       promedio suele ser una escisión o un error, no una noticia (HON −51% el 29-jun-2026
       con 2.6× su volumen; las noticias reales traen mucho más: MRNA +177% con 37×). No se
       borran; se reportan para que se vean en el dashboard.
    """
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
    g = df.groupby("symbol", sort=False)
    same = (df["open"] == g["open"].shift()) & (df["close"] == g["close"].shift())
    share = same.groupby(df["date"]).mean()
    dup_dates = sorted(share[share >= 0.8].index)
    if dup_dates:
        df = df[~df["date"].isin(dup_dates)].reset_index(drop=True)
        g = df.groupby("symbol", sort=False)
    ret = df["close"] / g["close"].shift() - 1
    vol_ratio = df["volume"] / g["volume"].transform(lambda v: v.shift().rolling(20, min_periods=5).mean())
    sus = df[(ret.abs() > 0.45) & (vol_ratio < 4)]
    report = {"dropped_duplicate_dates": [d.strftime("%Y-%m-%d") for d in dup_dates],
              "suspicious_moves": [{"date": r.date.strftime("%Y-%m-%d"), "symbol": r.symbol,
                                    "ret": round(float(ret[i]), 4)} for i, r in sus.iterrows()]}
    return df, report


def fetch_prices(symbols: list[str], start: str, providers: list[str], today: date) -> tuple[pd.DataFrame, dict]:
    """Devuelve (precios, meta). El histórico sale de OpenBB. Si a OpenBB le falta la
    sesión más reciente (a Cboe le pasa), se le pegan solo esas sesiones desde yfinance,
    verificando antes que las dos fuentes coincidan en el día que comparten.
    ``meta`` deja registrado qué pasó para que se vea en el dashboard."""
    symbols = sorted(set(symbols))
    expected = previous_weekday(today)  # la corrida es antes de la apertura
    openbb_providers = [p for p in providers if p != "yfinance"]
    attempts, df, label, dropped = [], None, "", []

    for provider in openbb_providers:
        try:
            df, dropped = _drop_partial_dates(_from_openbb(symbols, start, provider))
            label = f"OpenBB ({provider.capitalize()})"
            attempts.append({"provider": label, "ok": True, "last_date": df["date"].max().strftime("%Y-%m-%d")})
            break
        except Exception as exc:
            attempts.append({"provider": f"OpenBB ({provider.capitalize()})", "ok": False,
                             "error": f"{type(exc).__name__}: {exc}"[:300]})

    if "yfinance" in providers:
        if df is None:
            try:
                df, dropped = _drop_partial_dates(_from_yfinance(symbols, start))
                label = "yfinance (directo)"
                attempts.append({"provider": label, "ok": True, "last_date": df["date"].max().strftime("%Y-%m-%d")})
            except Exception as exc:
                attempts.append({"provider": "yfinance", "ok": False, "error": f"{type(exc).__name__}: {exc}"[:300]})
        elif df["date"].max().date() < expected:
            last = df["date"].max()
            try:
                recent = _from_yfinance(symbols, (last - pd.Timedelta(days=7)).strftime("%Y-%m-%d"))
                recent, _ = _drop_partial_dates(recent)
                both = df[df["date"] == last].merge(recent[recent["date"] == last], on="symbol", suffixes=("_a", "_b"))
                gap = float(((both["close_a"] / both["close_b"]) - 1).abs().median()) if len(both) else 1.0
                new = recent[(recent["date"] > last) & (recent["date"].dt.date <= expected)]
                if gap > 0.02:
                    attempts.append({"provider": "yfinance (parche)", "ok": False,
                                     "error": f"las fuentes difieren {gap:.1%} en {last:%Y-%m-%d}; no se mezclan"})
                elif len(new):
                    df = pd.concat([df, new], ignore_index=True)
                    label += " + yfinance (última sesión)"
                    attempts.append({"provider": "yfinance (parche)", "ok": True,
                                     "last_date": new["date"].max().strftime("%Y-%m-%d"), "rows_added": int(len(new))})
            except Exception as exc:
                attempts.append({"provider": "yfinance (parche)", "ok": False,
                                 "error": f"{type(exc).__name__}: {exc}"[:300]})

    if df is None:
        raise RuntimeError(f"ningún proveedor de datos respondió: {attempts}")
    df, cleaning = clean_prices(df)
    meta = _meta(df, symbols, label, expected)
    meta["cleaning"] = cleaning
    meta["attempts"] = attempts
    if dropped:
        meta["dropped_partial_dates"] = dropped
    return df.sort_values(["symbol", "date"]).reset_index(drop=True), meta


def fetch_earnings(today: date, min_market_cap: float) -> tuple[list[dict], dict]:
    """Empresas "en juego" por resultados, vía el calendario de OpenBB (proveedor Nasdaq,
    sin API key): las que reportan hoy antes de abrir y las que reportaron al cierre del
    día hábil anterior. De mayor a menor capitalización. Nunca tumba la corrida."""
    prev = previous_weekday(today)
    meta = {"provider": "OpenBB (Nasdaq)", "ok": True}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from openbb import obb
        res = obb.equity.calendar.earnings(start_date=prev.isoformat(), end_date=today.isoformat(), provider="nasdaq")
        df = res.to_dataframe().reset_index()
        df.columns = [str(c).lower() for c in df.columns]
        out = []
        for r in df.to_dict("records"):
            sym, when = str(r.get("symbol") or "").upper(), str(r.get("reporting_time") or "").lower()
            day = pd.Timestamp(r.get("report_date")).date()
            cap = float(r.get("market_cap") or 0)
            if not re.fullmatch(r"[A-Z]{1,5}", sym) or cap < min_market_cap:
                continue
            if day == today and "pre" in when:
                out.append({"symbol": sym, "name": r.get("name"), "when": "reporta hoy antes de abrir", "market_cap": cap})
            elif day == prev and "after" in when:
                out.append({"symbol": sym, "name": r.get("name"), "when": "reportó ayer al cierre", "market_cap": cap})
        out.sort(key=lambda e: e["market_cap"], reverse=True)
        meta["found"] = len(out)
        return out, meta
    except Exception as exc:
        meta.update(ok=False, error=f"{type(exc).__name__}: {exc}"[:300], found=0)
        return [], meta


def last_closes(prices: pd.DataFrame) -> dict[str, float]:
    last = prices.sort_values("date").groupby("symbol").tail(1)
    return {r.symbol: float(r.close) for r in last.itertuples()}
