"""Etapa 2 · Ranking cuantitativo con Qlib (costo: $0).

Recibe los precios de OpenBB, los vuelca al formato binario de Qlib y usa su motor de
expresiones para calcular el momentum de 12 meses sin el último mes:

    Ref($close, 21) / Ref($close, 252) - 1

Es el factor que documentaron Jegadeesh y Titman (1993). Las 10 acciones con el valor más
alto forman el núcleo de la cartera.

Por qué este y no el modelo de 158 features (Alpha158 + Ridge) de la versión anterior: en
research/swing.py, las carteras armadas con ese modelo no se distinguieron de comprar todo
el universo por igual. El momentum sí salió por encima, pero casi toda esa ventaja venía
de las 15 acciones que hoy sabemos que ganaron (sesgo de supervivencia). Es una apuesta
respaldada por la literatura, no por estos datos.

``alpha158_features`` se queda para el banco de pruebas de research/.
"""
from __future__ import annotations

import shutil
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

FIELDS = ["open", "high", "low", "close", "volume", "vwap", "factor"]
MOMENTUM_EXPR = "Ref($close, 21) / Ref($close, 252) - 1"


def dump_to_qlib(prices: pd.DataFrame, universe: list[str], qlib_dir: Path) -> list[pd.Timestamp]:
    """Escribe el layout que lee Qlib: calendars/day.txt, instruments/all.txt y un .bin
    float32 por símbolo y campo, cuyo primer valor es el índice de inicio en el calendario."""
    if qlib_dir.exists():
        shutil.rmtree(qlib_dir)
    (qlib_dir / "calendars").mkdir(parents=True)
    (qlib_dir / "instruments").mkdir()
    calendar = sorted(prices["date"].unique())
    (qlib_dir / "calendars" / "day.txt").write_text(
        "\n".join(pd.Timestamp(d).strftime("%Y-%m-%d") for d in calendar) + "\n")
    cal_index = pd.DatetimeIndex(calendar)
    lines = []
    for sym, g in prices.groupby("symbol"):
        g = g.drop_duplicates("date").set_index("date").sort_index()
        g = g.reindex(cal_index[(cal_index >= g.index[0]) & (cal_index <= g.index[-1])])
        # Cboe no da VWAP: se aproxima con el precio típico (H+L+C)/3.
        g["vwap"] = (g["high"] + g["low"] + g["close"]) / 3
        g["factor"] = 1.0
        start = int(cal_index.get_loc(g.index[0]))
        out = qlib_dir / "features" / sym.lower()
        out.mkdir(parents=True)
        for field in FIELDS:
            np.hstack([[start], g[field].to_numpy(dtype="float64")]).astype("<f4").tofile(out / f"{field}.day.bin")
        if sym in universe:
            lines.append(f"{sym}\t{g.index[0]:%Y-%m-%d}\t{g.index[-1]:%Y-%m-%d}")
    (qlib_dir / "instruments" / "all.txt").write_text("\n".join(lines) + "\n")
    return [pd.Timestamp(d) for d in calendar]


def _init_qlib(prices: pd.DataFrame, universe: list[str], workdir: Path) -> list[pd.Timestamp]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import qlib
        from qlib.constant import REG_US

    calendar = dump_to_qlib(prices, universe, workdir / "qlib_data")
    qlib.init(provider_uri=str(workdir / "qlib_data"), region=REG_US, kernels=1,
              expression_cache=None, dataset_cache=None, logging_level=40)
    return calendar


def alpha158_features(prices: pd.DataFrame, universe: list[str], workdir: Path) -> pd.DataFrame:
    """Features Alpha158 de Qlib, normalizadas por fecha en corte transversal y acotadas a ±3."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from qlib.contrib.data.handler import Alpha158
        from qlib.data.dataset.handler import DataHandlerLP

    calendar = _init_qlib(prices, universe, workdir)
    handler = Alpha158(instruments="all", start_time=calendar[0], end_time=calendar[-1], infer_processors=[
        {"class": "CSZScoreNorm", "kwargs": {"fields_group": "feature"}},
        {"class": "Fillna", "kwargs": {"fields_group": "feature"}}], learn_processors=[])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        feat = handler.fetch(col_set="feature", data_key=DataHandlerLP.DK_I)
    feat.index = feat.index.set_names(["date", "symbol"])
    return feat.clip(-3, 3)


def zscore_by_date(y: pd.Series) -> pd.Series:
    return y.groupby(level="date").transform(lambda s: (s - s.mean()) / (s.std() or 1.0))


def qlib_momentum(prices: pd.DataFrame, universe: list[str], workdir: Path) -> pd.Series:
    """Momentum 12-1 de la última fecha, calculado por el motor de expresiones de Qlib."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from qlib.data import D

    calendar = _init_qlib(prices, universe, workdir)
    last = calendar[-1]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = D.features(D.instruments("all"), [MOMENTUM_EXPR], start_time=last, end_time=last)
    s = df.iloc[:, 0]
    s.index = [str(i).upper() for i in s.index.get_level_values("instrument")]
    return s.replace([np.inf, -np.inf], np.nan).dropna()


def pandas_momentum(prices: pd.DataFrame, universe: list[str]) -> pd.Series:
    """La misma fórmula en pandas: respaldo si Qlib falla, y la demo para ir rápido."""
    c = prices[prices["symbol"].isin(universe)].pivot(index="date", columns="symbol", values="close").sort_index()
    if len(c) <= 252:
        return pd.Series(dtype=float)
    return (c.iloc[-22] / c.iloc[-253] - 1).dropna()


def rank_universe(prices: pd.DataFrame, universe: list[str], workdir: Path, use_qlib: bool = True) -> dict:
    """Ranking del universo por momentum 12-1, de mayor a menor."""
    result: dict = {"engine": "Qlib (momentum 12-1)", "formula": MOMENTUM_EXPR,
                    "label": "retorno de los últimos 12 meses sin contar el último"}
    scores = None
    if use_qlib:
        try:
            scores = qlib_momentum(prices, universe, workdir)
            if scores.empty:
                raise RuntimeError("Qlib no devolvió valores (¿menos de 253 días de historia?)")
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"[:400]
            scores = None
    if scores is None:
        scores = pandas_momentum(prices, universe)
        result["engine"] = "pandas (momentum 12-1)" if use_qlib is False else "respaldo en pandas (momentum 12-1)"
    result["as_of"] = pd.Timestamp(prices["date"].max()).strftime("%Y-%m-%d")
    ordered = scores.sort_values(ascending=False)
    result["ranking"] = [{"symbol": s, "score": round(float(v), 6), "rank": i + 1} for i, (s, v) in enumerate(ordered.items())]
    return result
