"""Banco de pruebas gratis: ¿qué parte del bot tiene evidencia a favor?

Todo se evalúa caminando hacia adelante (el modelo solo ve el pasado) y siempre sobre lo
mismo que operaría el bot: entrar en la apertura y salir el mismo día.

    python -m research.evaluate               # universo de config.yaml
    python -m research.evaluate --wide        # universo ampliado (~120 acciones)

Escribe research/results[_wide].json. No usa LLM ni llaves.
"""
from __future__ import annotations

import argparse
import json
import tempfile
import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from bot.config import ROOT, load_config
from bot.data import clean_prices, fetch_prices
from bot.qlib_signals import alpha158_features, zscore_by_date

WIDE = """LIN ACN TMO ABT DHR WFC MS C AXP BLK SCHW SPGI PM MO T VZ CMCSA TMUS IBM NOW INTU AMAT MU LRCX KLAC
ADI PANW SNPS CDNS UBER ABNB BKNG SBUX LOW TJX TGT GE HON RTX LMT UPS FDX DE UNP MMM COP SLB EOG PFE BMY AMGN
GILD ISRG MDT CVS CI ELV PYPL SHOP COIN PLTR SNOW CRWD MRVL SMCI ARM RIVN F GM DAL UAL CCL MRNA ROKU DKNG HOOD
SOFI NET DDOG ZS""".split()

K = 5            # tickers por lado
STEP = 20        # días entre reentrenamientos
MIN_TRAIN = 400  # días mínimos de historia para el primer modelo
ALPHA = 1000.0


def mask_suspicious(prices: pd.DataFrame, O, H, L, C):
    """Escisiones y errores: se reescala la historia previa al salto para que ese día no
    cuente como retorno (como haría un ajuste por escisión)."""
    _, rep = clean_prices(prices)
    O, H, L, C = (x.copy() for x in (O, H, L, C))
    for m in rep["suspicious_moves"]:
        d, s = pd.Timestamp(m["date"]), m["symbol"]
        if s not in C.columns or d not in C.index:
            continue
        i = C.index.get_loc(d)
        k = C[s].iloc[i] / C[s].iloc[i - 1]
        for x in (O, H, L, C):
            x.iloc[:i, x.columns.get_loc(s)] *= k
    return O, H, L, C


def walk_forward(feat: pd.DataFrame, label: pd.Series, embargo: int) -> pd.Series:
    """Ridge reentrenada cada STEP días; predice solo fechas que no vio."""
    from sklearn.linear_model import Ridge

    dates = feat.index.get_level_values("date").unique().sort_values()
    y = label.reindex(feat.index)
    y = zscore_by_date(y)
    out = []
    for start in range(MIN_TRAIN, len(dates), STEP):
        train_dates = dates[: start - embargo]
        test_dates = dates[start: start + STEP]
        tr = feat.index.get_level_values("date").isin(train_dates) & y.notna().to_numpy()
        te = feat.index.get_level_values("date").isin(test_dates)
        model = Ridge(alpha=ALPHA).fit(feat[tr].to_numpy(), y[tr].to_numpy())
        out.append(pd.Series(model.predict(feat[te].to_numpy()), index=feat.index[te]))
    return pd.concat(out)


def stats(daily: pd.Series) -> dict:
    daily = daily.dropna()
    if len(daily) < 2:
        return {"days": int(len(daily))}
    mean, sd = daily.mean(), daily.std()
    return {"days": int(len(daily)), "mean_bps": round(mean * 1e4, 2), "t": round(mean / sd * np.sqrt(len(daily)), 2),
            "sharpe": round(mean / sd * np.sqrt(252), 2), "hit": round(float((daily > 0).mean()), 3)}


def bracket_exit(side: int, o, h, l, c, stop, target):
    """Retorno de una entrada en la apertura con stop y objetivo en el mismo día. Si el
    rango del día toca los dos, se asume que tocó primero el stop (supuesto conservador)."""
    if side > 0:
        hit_stop, hit_tgt = l <= o - stop, h >= o + target
        px = np.where(hit_stop, o - stop, np.where(hit_tgt, o + target, c))
    else:
        hit_stop, hit_tgt = h >= o + stop, l <= o - target
        px = np.where(hit_stop, o + stop, np.where(hit_tgt, o - target, c))
    return side * (px / o - 1)


def evaluate(wide: bool) -> dict:
    cfg = load_config()
    universe = sorted(set(cfg["universe"] + (WIDE if wide else [])))
    cache = ROOT / ".cache" / f"prices_{'wide' if wide else 'base'}.parquet"
    if cache.exists():
        prices, _ = clean_prices(pd.read_parquet(cache))
    else:
        prices, _ = fetch_prices(universe + [cfg["benchmark"]], cfg["data"]["history_start"], ["cboe"], date.today())
        cache.parent.mkdir(exist_ok=True)
        prices.to_parquet(cache)
    universe = [s for s in universe if s in set(prices["symbol"])]
    counts = prices.groupby("symbol")["date"].count()
    universe = [s for s in universe if counts[s] >= 0.9 * counts.max()]  # historia completa
    px = prices[prices["symbol"].isin(universe)]
    P = {f: px.pivot(index="date", columns="symbol", values=f).sort_index() for f in ("open", "high", "low", "close", "volume")}
    O, H, L, C, V = P["open"], P["high"], P["low"], P["close"], P["volume"]
    O, H, L, C = mask_suspicious(prices, O, H, L, C)

    # Lo que se puede saber al cierre de t sobre la sesión t+1
    intraday_next = (C / O - 1).shift(-1)
    overnight_next = (O.shift(-1) / C - 1)
    fwd5 = O.shift(-6) / O.shift(-1) - 1
    tr = pd.concat([(H - L).stack(), (H - C.shift()).abs().stack(), (L - C.shift()).abs().stack()], axis=1).max(axis=1).unstack()
    atr = tr.rolling(14).mean()

    res: dict = {"universe": len(universe), "wide": wide, "from": str(C.index[0].date()), "to": str(C.index[-1].date()),
                 "k_per_side": K, "retrain_every_days": STEP}

    # 0 · ¿dónde está el retorno: en la sesión o en la noche?
    spy = prices[prices["symbol"] == cfg["benchmark"]].set_index("date").sort_index()
    res["where_returns_come_from"] = {
        "universe_intraday": stats(intraday_next.mean(axis=1)), "universe_overnight": stats(overnight_next.mean(axis=1)),
        "spy_intraday": stats(spy["close"] / spy["open"] - 1), "spy_overnight": stats(spy["open"] / spy["close"].shift() - 1)}

    with tempfile.TemporaryDirectory() as tmp:
        feat = alpha158_features(prices, universe, Path(tmp))

    def long_format(df):
        s = df.stack()
        s.index = s.index.set_names(["date", "symbol"])
        return s

    y_oc, y_5 = long_format(intraday_next), long_format(fwd5)
    preds = {"qlib_intraday": walk_forward(feat, y_oc, embargo=2), "qlib_5d": walk_forward(feat, y_5, embargo=7)}
    test_dates = preds["qlib_intraday"].index.get_level_values("date").unique()
    ret1 = (C / C.shift() - 1)
    preds["reversal_1d"] = long_format(-ret1).reindex(preds["qlib_intraday"].index)
    preds["momentum_20d"] = long_format(C / C.shift(20) - 1).reindex(preds["qlib_intraday"].index)
    rng = np.random.default_rng(0)
    preds["random"] = pd.Series(rng.normal(size=len(preds["qlib_intraday"])), index=preds["qlib_intraday"].index)

    res["test_days"] = int(len(test_dates))
    res["signals"] = {}
    picks = {}
    for name, p in preds.items():
        frame = pd.concat([p.rename("p"), y_oc.rename("y")], axis=1).dropna()
        ic = frame.groupby(level="date").apply(lambda d: d["p"].corr(d["y"], method="spearman"))
        rank = frame.groupby(level="date")["p"].rank(ascending=False, method="first")
        n = frame.groupby(level="date")["p"].transform("size")
        long_leg = frame["y"][rank <= K].groupby(level="date").mean()
        short_leg = -frame["y"][rank > n - K].groupby(level="date").mean()
        ls = (long_leg + short_leg) / 2
        picks[name] = (rank, n)
        res["signals"][name] = {
            "rank_ic": round(float(ic.mean()), 4), "rank_ic_t": round(float(ic.mean() / ic.std() * np.sqrt(len(ic))), 2),
            "long_top": stats(long_leg), "short_bottom": stats(short_leg), "long_short": stats(ls),
            "long_short_after_cost": {f"{c}bps_por_lado": stats(ls - 2 * c / 1e4) for c in (1, 2, 5)}}

    # ¿Sirven el stop y el objetivo? Se prueban sobre las mismas entradas de la señal intradía.
    rank, n = picks["qlib_intraday"]
    idx = rank.index
    d1 = {name: long_format(df.shift(-1)).reindex(idx) for name, df in (("o", O), ("h", H), ("l", L), ("c", C))}
    a = long_format(atr).reindex(idx)
    side = pd.Series(np.where(rank <= K, 1, np.where(rank > n - K, -1, 0)), index=idx)
    live = (side != 0) & a.notna() & d1["o"].notna()
    res["brackets"] = {}
    for stop_k, tgt_k in ((None, None), (0.5, 1.0), (1.0, 1.0), (1.0, 2.0), (1.5, 3.0), (2.0, 4.0)):
        o, h, l, c, s, at = (x[live].to_numpy() for x in (d1["o"], d1["h"], d1["l"], d1["c"], side, a))
        if stop_k is None:
            r = s * (c / o - 1)
        else:
            r = np.where(s > 0, bracket_exit(1, o, h, l, c, stop_k * at, tgt_k * at),
                         bracket_exit(-1, o, h, l, c, stop_k * at, tgt_k * at))
        daily = pd.Series(r, index=idx[live]).groupby(level="date").mean()
        key = "sin_bracket (salir al cierre)" if stop_k is None else f"stop {stop_k} ATR / objetivo {tgt_k} ATR"
        res["brackets"][key] = {**stats(daily), "worst_day_bps": round(float(daily.min()) * 1e4, 1),
                                "std_bps": round(float(daily.std()) * 1e4, 1)}

    # El bot manda el bracket antes de la apertura, así que los niveles se anclan al cierre
    # previo y no al precio de entrada. Si la apertura ya salta un nivel, sale de inmediato.
    pc = long_format(C).reindex(idx)
    for stop_k, tgt_k in ((1.0, 2.0), (1.5, 3.0)):
        o, h, l, c, s_, at, base = (x[live].to_numpy() for x in (d1["o"], d1["h"], d1["l"], d1["c"], side, a, pc))
        up, dn = np.where(s_ > 0, base + tgt_k * at, base + stop_k * at), np.where(s_ > 0, base - stop_k * at, base - tgt_k * at)
        gapped = (o >= up) | (o <= dn)
        first_dn = l <= dn   # se asume que el nivel adverso se toca primero
        px = np.where(gapped, o, np.where(s_ > 0, np.where(first_dn, dn, np.where(h >= up, up, c)),
                                          np.where(h >= up, up, np.where(first_dn, dn, c))))
        daily = pd.Series(s_ * (px / o - 1), index=idx[live]).groupby(level="date").mean()
        res["brackets"][f"anclado al cierre previo: stop {stop_k} / objetivo {tgt_k} ATR"] = {
            **stats(daily), "worst_day_bps": round(float(daily.min()) * 1e4, 1), "std_bps": round(float(daily.std()) * 1e4, 1),
            "gapped_share": round(float(gapped.mean()), 3)}

    # Acciones "en juego": ayer se movieron más de 1.5 ATR con volumen de más de 1.5 veces su
    # promedio. ¿Hoy siguen en la misma dirección, se revierten, o solo se mueven más?
    move = (C / C.shift() - 1) / (atr / C)
    hot = (move.abs() > 1.5) & (V / V.rolling(20).mean() > 1.5)
    cont = (np.sign(move) * intraday_next).where(hot)
    rng_next = ((H - L) / O).shift(-1)
    res["in_play"] = {
        "events": int(hot.sum().sum()), "events_per_day": round(float(hot.sum(axis=1).mean()), 2),
        "continuation_next_intraday": stats(cont.mean(axis=1)),
        "after_up_day": stats(intraday_next.where(hot & (move > 0)).mean(axis=1)),
        "after_down_day": stats(intraday_next.where(hot & (move < 0)).mean(axis=1)),
        "next_day_range_pct_in_play": round(float(rng_next.where(hot).stack().mean()) * 100, 2),
        "next_day_range_pct_others": round(float(rng_next.where(~hot).stack().mean()) * 100, 2)}
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wide", action="store_true")
    args = ap.parse_args()
    out = evaluate(args.wide)
    path = ROOT / "research" / f"results{'_wide' if args.wide else ''}.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
