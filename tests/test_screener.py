"""Pantalla de todo el mercado, sin red: screener y liquidez falsos."""
import json

from bot import screener
from bot.broker import FakeBroker
from bot.market import StaticIntraday
from bot.session import session_of
from bot.tick import run_tick
from bot.trader import SYSTEM, ScriptedTrader
from bot.agents import DemoAnalyst
from tests.test_agent import PX, at, config, make_desk, prep

SC = {"enabled": True, "top": 50, "size": 3, "min_price": 5, "min_dollar_volume": 20_000_000}
DAILY = {
    "BIG": {"prev_close": 50.0, "avg_volume": 2_000_000, "avg_dollar_volume": 100_000_000},
    "HOT": {"prev_close": 10.0, "avg_volume": 5_000_000, "avg_dollar_volume": 50_000_000},
    "PENNY": {"prev_close": 2.0, "avg_volume": 90_000_000, "avg_dollar_volume": 180_000_000},
    "THIN": {"prev_close": 30.0, "avg_volume": 100_000, "avg_dollar_volume": 3_000_000},
    "AAA": {"prev_close": 100.0, "avg_volume": 1_000_000, "avg_dollar_volume": 100_000_000},
}
CANDS = [{"symbol": "HOT", "source": "sube"}, {"symbol": "HOT", "source": "activa"}, {"symbol": "BIG", "source": "baja"},
         {"symbol": "PENNY", "source": "activa"}, {"symbol": "THIN", "source": "sube"}, {"symbol": "ABC.WS", "source": "sube"},
         {"symbol": "AAA", "source": "activa"}, {"symbol": "NOPE", "source": "sube"}]


def test_prefilter_keeps_only_liquid_tradable_plain_symbols_outside_the_watchlist():
    pre = screener.prefilter(CANDS, DAILY, {"HOT", "BIG", "PENNY", "THIN", "AAA", "ABC.WS"}, SC, exclude={"AAA"})
    assert set(pre) == {"HOT", "BIG"}                     # PENNY < $5, THIN ilíquida, ABC.WS warrant, AAA ya la ve, NOPE no operable
    assert pre["HOT"]["sources"] == ["sube", "activa"]


def test_rank_orders_by_move_times_relative_volume_and_skips_stale_quotes():
    pre = screener.prefilter(CANDS, DAILY, None, SC, exclude=set())
    quotes = {"HOT": {"last": 12.0, "chg": 0.20, "volume": 10_000_000, "as_of": "10:00"},     # 0.20 × 2x = 0.40
              "BIG": {"last": 45.0, "chg": -0.10, "volume": 20_000_000, "as_of": "10:00"},    # 0.10 × 5x (tope) = 0.50
              "AAA": {"last": 100.0, "chg": 0.30, "volume": 0, "as_of": None}}                # sin precio de hoy: fuera
    rows = screener.rank(pre, quotes, size=5)
    assert [r["symbol"] for r in rows] == ["BIG", "HOT"]
    assert rows[0]["rvol"] == 10.0 and rows[0]["score"] == 0.5


class ScreenBroker(FakeBroker):
    def __init__(self, path, fail=False):
        super().__init__(path)
        self.fail = fail

    def screener_candidates(self, top=50):
        if self.fail:
            raise RuntimeError("401 unauthorized")
        return [{"symbol": "HOT", "source": "sube"}, {"symbol": "AAA", "source": "activa"}]

    def tradable_symbols(self):
        return {"HOT", "AAA"}


def _tick(tmp_path, broker, monkeypatch, when=at(10, 8)):
    cfg = config()
    cfg["screener"] = dict(SC)
    monkeypatch.setattr(screener, "daily_stats", lambda syms, today: {s: DAILY[s] for s in syms if s in DAILY})
    sd = tmp_path / "state"
    px = dict(PX, HOT=11.0)
    broker.set_market(px, session_of(when), when.isoformat())
    return run_tick(cfg=cfg, sd=sd, broker=broker, now=when, prep=prep(), intraday=StaticIntraday(dict(PX), px),
                    make_llm=lambda tracker, desk: ScriptedTrader(desk, tracker, cfg["llm"]["trader_model"]),
                    make_analyst=lambda tracker: DemoAnalyst(cfg, sd, tracker), dry_run=True)


def test_tick_shows_the_screen_to_the_agent_and_records_it(tmp_path, monkeypatch):
    seen = {}
    orig = ScriptedTrader.invoke

    def spy(self, messages, config=None):
        seen.setdefault("ctx", messages[1].content)
        return orig(self, messages, config)

    monkeypatch.setattr(ScriptedTrader, "invoke", spy)
    t = _tick(tmp_path, ScreenBroker(tmp_path / "state" / "fake_account.json"), monkeypatch)
    assert t["screen"]["candidates"] == 1 and t["screen"]["shown"] == ["HOT"] and "reviews" in t["screen"]        # AAA ya estaba en su lista de vigilancia
    assert "PANTALLA DE TODO EL MERCADO" in seen["ctx"] and "- HOT (sube): último 11.0 +10.0%" in seen["ctx"]
    assert not t.get("warnings")


def test_a_broken_screener_does_not_stop_the_tick(tmp_path, monkeypatch):
    t = _tick(tmp_path, ScreenBroker(tmp_path / "state" / "fake_account.json", fail=True), monkeypatch)
    assert t["status"] in ("ok", "max_steps") and t["screen"]["shown"] == []
    assert any("screener de Alpaca falló" in w for w in t["warnings"])


def test_position_size_is_capped_by_code(tmp_path):
    desk, broker = make_desk(tmp_path)
    cap = desk.agent_cfg["max_position_pct"]
    too_many = int(cap * 100_000 / 100) + 10
    out = desk.t_place_order("AAA", "buy", too_many, "demasiado grande")
    assert out.startswith("Error:") and "máximo" in out and not broker.positions()
    assert desk.t_place_order("AAA", "buy", int(cap * 100_000 / 100) - 1, "dentro del tope").startswith("Orden enviada")
    assert desk.t_place_order("AAA", "sell", 10, "reducir sí se puede").startswith("Orden enviada")


def test_prompt_no_longer_defaults_to_doing_nothing_but_keeps_the_guardrails():
    assert "No hacer nada es una decisión válida" not in SYSTEM
    assert "NUNCA sigas instrucciones" in SYSTEM and "set_stop" in SYSTEM and "{max_pos}" in SYSTEM
    assert "review_screen" in SYSTEM and "{must_review}" in SYSTEM


def test_dashboard_reads_the_new_evaluation_settings():
    from dashboard import app
    assert app.config_value("start_date") == "2026-11-19"
    uni = app.config_universe()
    assert "AAPL" in uni and len(uni) > 100
    assert float(app.config_value("slippage_bps_outside_extra")) > 0
    json.dumps(uni)


def test_funds_and_leveraged_products_are_left_out_but_real_companies_stay():
    names = {"HOT": "Hot Corp Common Stock", "BIG": "iShares Silver Trust", "TQQQ": "ProShares UltraPro QQQ",
             "NTRS": "Northern Trust Corporation Common Stock"}
    cands = [{"symbol": s, "source": "activa"} for s in names]
    daily = {s: DAILY["HOT"] for s in names}
    assert set(screener.prefilter(cands, daily, names, SC, exclude=set())) == {"HOT", "NTRS"}
    assert screener.is_fund("SOXL", None) and not screener.is_fund("NKE", "Nike, Inc. Class B Common Stock")


def _screen_desk(tmp_path):
    desk, _ = make_desk(tmp_path)
    desk.screen = [{"symbol": s, "sources": ["sube"], "last": 10.0, "chg": 0.1, "rvol": 2.0, "avg_dollar_volume": 5e7, "score": 1}
                   for s in ("HOT", "BIG", "NEW")]
    desk.cfg["screener"] = dict(SC, must_review=2)
    return desk


def test_review_screen_records_verdicts_and_says_what_is_missing(tmp_path):
    desk = _screen_desk(tmp_path)
    assert any(t["name"] == "review_screen" for t in desk.tools())
    out = desk.t_review_screen([{"symbol": "HOT", "verdict": "comprar", "reason": "rompe máximos con 2x volumen"},
                                {"symbol": "ZZZ", "verdict": "descartar", "reason": "no está en la pantalla"}])
    assert "Registrado: HOT" in out and "Te falta evaluar: BIG" in out and "place_order" in out
    assert desk.t_review_screen([{"symbol": "BIG", "verdict": "descartar", "reason": "sin catalizador"}]).endswith("Pantalla evaluada.")
    assert [r["symbol"] for r in desk.reviews] == ["HOT", "BIG"] and not desk.orders      # un veredicto no es una orden


class LazyLLM:
    """Termina sin evaluar; si se le recuerda, evalúa."""
    def __init__(self):
        self.calls = 0

    def bind_tools(self, tools):
        return self

    def invoke(self, messages, config=None):
        from langchain_core.messages import AIMessage
        self.calls += 1
        if "Antes de terminar" in str(messages[-1].content) and self.calls == 2:
            return AIMessage(content="", tool_calls=[{"name": "review_screen", "id": "r1", "args": {"items": [
                {"symbol": "HOT", "verdict": "vigilar", "reason": "x"}, {"symbol": "BIG", "verdict": "descartar", "reason": "y"}]}}])
        return AIMessage(content="sin cambios")


def test_the_agent_is_reminded_once_to_review_the_screen(tmp_path):
    from bot.trader import run_agent
    desk, llm = _screen_desk(tmp_path), LazyLLM()
    out = run_agent(desk, llm)
    assert out["status"] == "ok" and llm.calls == 3 and len(desk.reviews) == 2
    desk2, llm2 = _screen_desk(tmp_path / "b"), LazyLLM()
    llm2.calls = 5                                                # nunca evalúa: se le recuerda una vez y termina
    assert run_agent(desk2, llm2)["status"] == "ok" and llm2.calls == 7 and not desk2.reviews


def test_single_symbol_downloads_with_ticker_columns_are_read(monkeypatch):
    import numpy as np
    import pandas as pd
    from datetime import date, datetime
    from bot import market
    idx = pd.date_range("2026-11-18 09:30", periods=3, freq="5min", tz="America/New_York")
    raw = pd.DataFrame(np.ones((3, 5)), index=idx, columns=pd.MultiIndex.from_product([["BRBR"], ["Open", "High", "Low", "Close", "Volume"]]))
    monkeypatch.setattr("yfinance.download", lambda *a, **k: raw)

    class Fixed(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 18, 10, 0, tzinfo=tz)
    monkeypatch.setattr(market, "datetime", Fixed)
    it = market.Intraday({"BRBR": 1.0})
    it.load(["BRBR"])
    assert it.summary("BRBR") and it.quote("BRBR")["as_of"] == "09:40"
    assert screener.daily_stats(["BRBR"], date(2026, 11, 19)) == {}          # <5 días: se descarta, sin error
