"""Datos, Qlib, bitácora y candado de paper: las piezas que no dependen del agente."""
import numpy as np
import pandas as pd
import pytest

from bot.broker import PAPER_HOST, AlpacaPaperBroker
from bot.data import clean_prices
from bot.journal import backfill_research, record_fills, round_trips, update_journal, update_virtual
from bot.qlib_signals import dump_to_qlib, pandas_momentum, qlib_momentum
from bot.state import save_json


def synthetic_prices(symbols, days=320, seed=3, end="2026-11-20"):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=end, periods=days)
    rows = []
    for i, s in enumerate(symbols):
        close = 100 * np.exp(np.cumsum(rng.normal(0.0008 * (i % 7 - 3), 0.02, days)))
        for d, c in zip(dates, close):
            o = c * (1 + rng.normal(0, 0.005))
            rows.append({"date": d, "symbol": s, "open": o, "high": max(o, c) * 1.006, "low": min(o, c) * 0.994,
                         "close": c, "volume": 1e6 * (1 + rng.random())})
    return pd.DataFrame(rows)


def test_round_trips_fifo_across_days_and_partial_exits(tmp_path):
    fills = [
        {"symbol": "AAA", "side": "buy", "qty": 10, "price": 100.0, "at": "2026-11-02T14:30:00+00:00", "id": "1"},
        {"symbol": "AAA", "side": "buy", "qty": 10, "price": 110.0, "at": "2026-11-05T14:30:00+00:00", "id": "2"},
        {"symbol": "AAA", "side": "sell", "qty": 15, "price": 120.0, "at": "2026-11-12T14:30:00+00:00", "id": "3"},
        {"symbol": "BBB", "side": "buy", "qty": 5, "price": 50.0, "at": "2026-11-03T14:30:00+00:00", "id": "4"},
    ]
    closed, open_lots = round_trips(fills)
    assert [(t["qty"], t["entry"], t["pnl_usd"], t["days"]) for t in closed] == [(10, 100.0, 200.0, 8), (5, 110.0, 50.0, 5)]
    assert open_lots["AAA"][0]["qty"] == 5 and open_lots["BBB"][0]["qty"] == 5
    sd = tmp_path / "s"
    assert record_fills(sd, fills) == 4 and record_fills(sd, fills) == 0
    assert len(update_journal(sd)) == 2


def test_qlib_momentum_matches_the_pandas_formula(tmp_path):
    prices = synthetic_prices([f"S{i}" for i in range(6)] + ["BMK"], days=300)
    uni = [f"S{i}" for i in range(6)]
    q, p = qlib_momentum(prices, uni, tmp_path), pandas_momentum(prices, uni)
    assert set(q.index) == set(p.index) == set(uni)
    assert (q - p.reindex(q.index)).abs().max() < 1e-5


def test_alpaca_client_is_locked_to_the_paper_host(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "llave-de-prueba")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "secreto-de-prueba")
    assert PAPER_HOST in str(AlpacaPaperBroker().client._base_url.value)


def test_qlib_dump_layout(tmp_path):
    prices = synthetic_prices(["AAA", "BBB", "BMK"], days=30)
    cal = dump_to_qlib(prices, ["AAA", "BBB"], tmp_path / "q")
    assert len(cal) == 30
    assert (tmp_path / "q/instruments/all.txt").read_text().count("\n") == 2
    raw = np.fromfile(tmp_path / "q/features/aaa/close.day.bin", dtype="<f4")
    assert raw[0] == 0 and len(raw) == 31
    assert raw[-1] == pytest.approx(prices[prices.symbol == "AAA"].close.iloc[-1], rel=1e-5)


def test_cleaning_drops_duplicate_holiday_and_flags_quiet_jumps():
    rows = []
    for i, d in enumerate(pd.bdate_range("2026-01-01", periods=30)):
        for s in ("AAA", "BBB", "CCC", "DDD", "EEE"):
            px = 100 + i + (0 if s != "EEE" or i < 25 else -70)        # EEE: -56% con volumen normal
            rows.append({"date": d, "symbol": s, "open": px, "high": px, "low": px, "close": px, "volume": 1e6})
    df = pd.DataFrame(rows)
    dup = df[df.date == df.date.max()].assign(date=df.date.max() + pd.Timedelta(days=1))
    out, rep = clean_prices(pd.concat([df, dup]))
    assert len(rep["dropped_duplicate_dates"]) == 1 and out.date.nunique() == 30
    assert [m["symbol"] for m in rep["suspicious_moves"]] == ["EEE"]


def test_rule_benchmark_follows_each_days_core_and_spy(tmp_path):
    prices = synthetic_prices(["AAA", "BBB", "CCC", "BMK"], days=30)
    d = sorted(prices["date"].unique())
    first, switch = pd.Timestamp(d[20]), pd.Timestamp(d[25])
    save_json(tmp_path / "days" / f"{first:%Y-%m-%d}.json", {"date": f"{first:%Y-%m-%d}", "prep": {"rule_core": ["AAA", "BBB"]}})
    save_json(tmp_path / "days" / f"{switch:%Y-%m-%d}.json", {"date": f"{switch:%Y-%m-%d}", "prep": {"rule_core": ["CCC"]}})
    assert update_virtual(tmp_path, prices, "BMK") == 10
    rows = {r["date"]: r for r in __import__("json").loads((tmp_path / "virtual.json").read_text())}
    c = prices.pivot(index="date", columns="symbol", values="close").pct_change()
    assert rows[f"{first:%Y-%m-%d}"]["core_ret"] == pytest.approx(c.loc[first, ["AAA", "BBB"]].mean(), abs=1e-6)
    assert rows[f"{switch:%Y-%m-%d}"]["core_ret"] == pytest.approx(c.loc[switch, "CCC"], abs=1e-6)
    assert rows[f"{switch:%Y-%m-%d}"]["spy_ret"] == pytest.approx(c.loc[switch, "BMK"], abs=1e-6)


def test_research_outcome_is_filled_only_after_the_horizon(tmp_path):
    prices = synthetic_prices(["AAA", "BMK"], days=40)
    d = [pd.Timestamp(x) for x in sorted(prices["date"].unique())]
    save_json(tmp_path / "research.json", [{"date": f"{d[20]:%Y-%m-%d}", "symbol": "AAA", "rating": "Buy"},
                                           {"date": f"{d[35]:%Y-%m-%d}", "symbol": "AAA", "rating": "Sell"}])
    assert backfill_research(tmp_path, prices, "BMK", 10) == 1
    old, new = __import__("json").loads((tmp_path / "research.json").read_text())
    c = prices.pivot(index="date", columns="symbol", values="close")
    assert old["fwd_ret"] == pytest.approx(c["AAA"].iloc[29] / c["AAA"].iloc[19] - 1, abs=1e-5)
    assert "fwd_ret" not in new
    assert backfill_research(tmp_path, prices, "BMK", 10) == 0          # no se recalcula


def test_saved_json_never_contains_nan(tmp_path):
    import json

    save_json(tmp_path / "x.json", {"a": float("nan"), "b": [1.5, float("inf")], "c": {"d": float("-inf")}})
    text = (tmp_path / "x.json").read_text()
    assert "NaN" not in text and "Infinity" not in text
    assert json.loads(text) == {"a": None, "b": [1.5, None], "c": {"d": None}}
