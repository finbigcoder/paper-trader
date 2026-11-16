"""Banco de pruebas para el modo que MANTIENE posiciones de un día a otro (gratis, sin LLM).

Contabilidad diaria: la señal se calcula con el cierre de t y se opera en la apertura de
t+1. En un día de rebalanceo los pesos viejos ganan la noche (cierre→apertura) y los
nuevos ganan la sesión (apertura→cierre). Entre rebalanceos los pesos se mantienen fijos
(aproximación: no se modela la deriva de pesos). Costo: 2 pb por lado sobre la rotación.

    python -m research.swing            # escribe research/results_swing.json

ADVERTENCIA: el universo son 119 acciones grandes HOY. Eso infla cualquier estrategia que
compre "el universo" (sesgo de supervivencia). Las comparaciones limpias son contra la
canasta igualitaria del mismo universo, no contra SPY.
"""
from __future__ import annotations

import json
import tempfile
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from bot.config import ROOT, load_config
from bot.qlib_signals import alpha158_features
from bot.data import clean_prices
from research.evaluate import WIDE, mask_suspicious, walk_forward

COST = 2 / 1e4          # por lado
MARGIN_RATE = 0.065     # tasa de margen de Alpaca para cuentas no-elite (docs, nov 2026)


def perf(daily: pd.Series) -> dict:
    daily = daily.dropna()
    eq = (1 + daily).cumprod()
    years = len(daily) / 252
    dd = eq / eq.cummax() - 1
    sd = daily.std()
    return {"days": int(len(daily)), "total": round(float(eq.iloc[-1] - 1), 4),
            "cagr": round(float(eq.iloc[-1] ** (1 / years) - 1), 4) if years > 0 else None,
            "vol": round(float(sd * np.sqrt(252)), 4), "sharpe": round(float(daily.mean() / sd * np.sqrt(252)), 2) if sd else None,
            "max_dd": round(float(dd.min()), 4)}


def excess(a: pd.Series, b: pd.Series) -> dict:
    d = (a - b).dropna()
    return {"mean_bps_day": round(float(d.mean() * 1e4), 2), "t": round(float(d.mean() / d.std() * np.sqrt(len(d))), 2),
            "ann": round(float(d.mean() * 252), 4)}


def run_weights(W: pd.DataFrame, O: pd.DataFrame, C: pd.DataFrame, rebal_days: pd.Index) -> pd.Series:
    """W: pesos objetivo indexados por la fecha de la SEÑAL (cierre). Se aplican desde la
    apertura del día siguiente y se mantienen hasta el siguiente rebalanceo."""
    dates = C.index
    on = (O / C.shift() - 1).fillna(0)        # noche: cierre previo → apertura
    intra = (C / O - 1).fillna(0)            # sesión: apertura → cierre
    target = W.reindex(dates).shift(1)       # señal de t se opera en t+1
    is_rebal = pd.Series(dates.isin(rebal_days), index=dates).shift(1, fill_value=False)
    held = target.where(is_rebal).ffill().fillna(0)
    prev = held.shift(1).fillna(0)
    ret = (prev * on).sum(axis=1) + (held * intra).sum(axis=1)
    # en días sin rebalanceo prev == held, así que lo anterior es cierre→cierre
    turnover = (held - prev).abs().sum(axis=1)
    return ret - turnover * COST


def lever(r: pd.Series, k: float) -> pd.Series:
    return k * r - max(k - 1, 0) * MARGIN_RATE / 252


def topk_weights(score: pd.DataFrame, k: int, every: int, start: int = 0, bottom: bool = False) -> tuple[pd.DataFrame, pd.Index]:
    dates = score.dropna(how="all").index
    rebal = dates[start::every]
    rk = score.rank(axis=1, ascending=bottom, method="first")
    W = (rk <= k).astype(float).div(k).where(score.notna(), 0.0)
    return W.loc[rebal], rebal


def with_stops(W: pd.DataFrame, rebal: pd.Index, O, H, L, C, atr, k_atr: float) -> pd.Series:
    """Como run_weights para carteras largas, pero cada posición tiene un stop fijo en
    entrada − k·ATR. Si lo toca sale (a la apertura si abrió por debajo) y queda en
    efectivo hasta el siguiente rebalanceo."""
    dates = C.index
    sig_to_trade = {d: dates[dates.get_loc(d) + 1] for d in rebal if dates.get_loc(d) + 1 < len(dates)}
    trade_days = set(sig_to_trade.values())
    w = pd.Series(0.0, index=C.columns)
    stops = pd.Series(np.nan, index=C.columns)
    out = []
    for i, d in enumerate(dates):
        if i == 0:
            out.append(0.0)
            continue
        pc, o, h, l, c = C.iloc[i - 1], O.iloc[i], H.iloc[i], L.iloc[i], C.iloc[i]
        r, cost = 0.0, 0.0
        if d in trade_days:
            sig = dates[i - 1]
            new = W.loc[sig].reindex(C.columns).fillna(0)
            r += (w * (o / pc - 1)).fillna(0).sum()
            cost = (new - w).abs().sum() * COST
            w = new
            stops = (o - k_atr * atr.iloc[i - 1]).where(w > 0)
            base = o
        else:
            base = pc
        live = w > 0
        hit = live & (l <= stops)
        exit_px = np.where(o <= stops, o, stops)
        px_end = pd.Series(np.where(hit, exit_px, c), index=C.columns)
        r += (w * (px_end / base - 1)).fillna(0).sum()
        if hit.any():
            cost += w[hit].sum() * COST
            w = w.where(~hit, 0.0)
        out.append(r - cost)
    return pd.Series(out, index=dates)


def main() -> None:
    cfg = load_config()
    prices, cleaning = clean_prices(pd.read_parquet(ROOT / ".cache" / "prices_wide.parquet"))
    universe = sorted(set(cfg["universe"] + WIDE) & set(prices["symbol"]))
    counts = prices.groupby("symbol")["date"].count()
    universe = [s for s in universe if counts[s] >= 0.9 * counts.max()]
    px = prices[prices["symbol"].isin(universe + ["SPY"])]
    P = {f: px.pivot(index="date", columns="symbol", values=f).sort_index() for f in ("open", "high", "low", "close")}
    O, H, L, C = mask_suspicious(prices, *(P[f] for f in ("open", "high", "low", "close")))
    Ou, Hu, Lu, Cu = (x[universe] for x in (O, H, L, C))
    tr = pd.concat([(Hu - Lu).stack(), (Hu - Cu.shift()).abs().stack(), (Lu - Cu.shift()).abs().stack()], axis=1).max(axis=1).unstack()
    atr = tr.rolling(14).mean()

    def stackit(df):
        s = df.stack()
        s.index = s.index.set_names(["date", "symbol"])
        return s

    with tempfile.TemporaryDirectory() as tmp:
        feat = alpha158_features(prices, universe, Path(tmp))
    fwd5 = Ou.shift(-6) / Ou.shift(-1) - 1
    fwd1 = (Cu / Ou - 1).shift(-1)
    q5 = walk_forward(feat, stackit(fwd5), embargo=7).unstack()
    q1 = walk_forward(feat, stackit(fwd1), embargo=2).unstack()
    test = q5.index
    start, end = test[0], test[-1]

    res: dict = {"universe": len(universe), "test_from": str(start.date()), "test_to": str(end.date()),
                 "cost_bps_per_side": COST * 1e4, "margin_rate": MARGIN_RATE,
                 "caveat": "universo elegido hoy: todo lo que compra 'el universo' tiene sesgo de supervivencia",
                 "cleaning": cleaning}
    S: dict[str, pd.Series] = {}
    spy = (C["SPY"] / C["SPY"].shift() - 1).loc[start:end]
    S["SPY"] = spy
    ew = Cu.pct_change(fill_method=None).mean(axis=1).loc[start:end]
    S["Universo igualitario (con sesgo)"] = ew

    def strat(name, W, rebal):
        S[name] = run_weights(W.reindex(columns=universe).fillna(0), Ou, Cu, rebal).loc[start:end]

    for k in (5, 10, 20):
        strat(f"Qlib 5d top-{k}, cada 5 días", *topk_weights(q5, k, 5))
    strat("Qlib 1d top-10, diario", *topk_weights(q1, 10, 1))
    mom20 = (Cu / Cu.shift(20) - 1).loc[test]
    strat("Momentum 20d top-10, cada 5 días", *topk_weights(mom20, 10, 5))
    mom12 = (Cu.shift(21) / Cu.shift(252) - 1).loc[test]
    strat("Momentum 12-1 top-10, cada 21 días", *topk_weights(mom12, 10, 21))
    Wb, rb = topk_weights(q5, 10, 5, bottom=True)
    S["Qlib 5d fondo-10 en CORTO, cada 5 días"] = (-run_weights(Wb.reindex(columns=universe).fillna(0), Ou, Cu, rb) - 2 * 0).loc[start:end]
    S["Núcleo 50% SPY + 50% Qlib top-10"] = 0.5 * spy + 0.5 * S["Qlib 5d top-10, cada 5 días"]

    for k in (5, 20):
        strat(f"Momentum 12-1 top-{k}, cada 21 días", *topk_weights(mom12, k, 21))
    strat("Momentum 12-1 top-10, cada 10 días", *topk_weights(mom12, 10, 10))
    S["Núcleo 50% SPY + 50% momentum 12-1 top-10"] = 0.5 * spy + 0.5 * S["Momentum 12-1 top-10, cada 21 días"]
    Wm, rm = topk_weights(mom12, 10, 21)
    for k_atr in (2.0, 3.0):
        S[f"Momentum 12-1 top-10 con stop {k_atr:g} ATR"] = with_stops(Wm.reindex(columns=universe).fillna(0), rm, Ou, Hu, Lu, Cu, atr, k_atr).loc[start:end]
    # ¿El momentum de este periodo es solo sesgo de supervivencia? Se repite quitando las 15
    # acciones que más subieron en todo el periodo (las que hoy "sabemos" que ganaron).
    winners = (Cu.loc[end] / Cu.loc[start] - 1).sort_values(ascending=False).index[:15].tolist()
    res["survivorship_check_removed"] = winners
    keep = [u for u in universe if u not in winners]
    Wk, rk_ = topk_weights(mom12[keep], 10, 21)
    S["Momentum 12-1 top-10 SIN las 15 más ganadoras"] = run_weights(Wk.reindex(columns=universe).fillna(0), Ou, Cu, rk_).loc[start:end]
    S["Universo igualitario SIN las 15 más ganadoras"] = Cu[keep].pct_change(fill_method=None).mean(axis=1).loc[start:end]
    S["Momentum 12-1 top-10 × 1.5"] = lever(S["Momentum 12-1 top-10, cada 21 días"], 1.5)
    W10, r10 = topk_weights(q5, 10, 5)
    for k_atr in (2.0, 3.0):
        S[f"Qlib 5d top-10 con stop {k_atr:g} ATR"] = with_stops(W10.reindex(columns=universe).fillna(0), r10, Ou, Hu, Lu, Cu, atr, k_atr).loc[start:end]

    for lv in (1.5, 2.0):
        S[f"SPY × {lv:g}"] = lever(spy, lv)
        S[f"Qlib 5d top-10 × {lv:g}"] = lever(S["Qlib 5d top-10, cada 5 días"], lv)
        S[f"Universo igualitario × {lv:g} (con sesgo)"] = lever(ew, lv)

    res["strategies"] = {k: perf(v) for k, v in S.items()}
    res["vs_universe_equal_weight"] = {k: excess(v, ew) for k, v in S.items() if ("Qlib" in k or "Momentum" in k) and "SIN" not in k}
    res["vs_universe_equal_weight"]["Momentum 12-1 top-10 SIN las 15 más ganadoras"] = excess(
        S["Momentum 12-1 top-10 SIN las 15 más ganadoras"], S["Universo igualitario SIN las 15 más ganadoras"])

    # Prueba de estrés del apalancamiento con 33 años de SPY (yfinance, ajustado por dividendos)
    import yfinance as yf

    long = yf.download("SPY", start="1993-02-01", auto_adjust=True, progress=False)["Close"].squeeze().pct_change().dropna()
    res["spy_long_history"] = {"from": str(long.index[0].date()), "to": str(long.index[-1].date())}
    for lv in (1.0, 1.25, 1.5, 2.0):
        r = lever(long, lv)
        eq = (1 + r).cumprod()
        yearly = (1 + r).groupby(r.index.year).prod() - 1
        res["spy_long_history"][f"x{lv:g}"] = {**perf(r), "worst_year": round(float(yearly.min()), 4),
                                                "worst_year_at": int(yearly.idxmin()),
                                                "dd_2008": round(float((eq["2007-10":"2009-03"] / eq["2007-10":"2009-03"].cummax() - 1).min()), 4),
                                                "dd_2020": round(float((eq["2020-02":"2020-04"] / eq["2020-02":"2020-04"].cummax() - 1).min()), 4),
                                                "dd_2022": round(float((eq["2022-01":"2022-10"] / eq["2022-01":"2022-10"].cummax() - 1).min()), 4),
                                                "cagr_if_borrow_3pct": perf(lv * long - max(lv - 1, 0) * 0.03 / 252)["cagr"]}
    out = ROOT / "research" / "results_swing.json"
    out.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main()
