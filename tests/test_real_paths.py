"""Las rutas "reales" (agentes, Alpaca y el job de media mañana) sin gastar ni tocar la
red: se construye el grafo de TradingAgents de verdad y se sustituye solo lo que
saldría a internet."""
import json
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from bot.agents import Analyst, headlines_from_news
from bot.broker import AlpacaPaperBroker
from bot.budget import BudgetExceeded, CostTracker
from bot.config import load_config

ACCOUNT = {"equity": 100_000.0, "cash": 5_000.0, "buying_power": 105_000.0}
POSITIONS = {"MU": {"qty": 30, "avg_price": 300.0}, "SPY": {"qty": 10, "avg_price": 600.0}}
PRICES = load_config()["prices"]


def fake(*replies, tracker=None):
    msgs = [AIMessage(content=r, usage_metadata={"input_tokens": 3000, "output_tokens": 200, "total_tokens": 3200},
                      response_metadata={"model_name": "claude-haiku-5-5"}) for r in replies]
    return GenericFakeChatModel(messages=iter(msgs), callbacks=[tracker] if tracker else None)


def test_headlines_are_extracted_and_trimmed():
    news = "## NVDA News\n\n### Titular uno (source: X)\nresumen largo\nLink: http://x\n\n### Titular   dos\notro\n### Tres"
    assert headlines_from_news(news, 2) == ["Titular uno (source: X)", "Titular dos"]


@pytest.fixture
def analyst(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-prueba-no-real")
    cfg = load_config()
    return Analyst(cfg, tmp_path / "state", tmp_path / "work", CostTracker(cfg["prices"], 1.0)), tmp_path / "state"


def test_graph_uses_configured_models_horizon_benchmark_and_our_tracker(analyst):
    a, _ = analyst
    cfg = load_config()
    assert a.graph.quick_thinking_llm.model == cfg["llm"]["quick_model"]
    assert a.graph.deep_thinking_llm.model == cfg["llm"]["deep_model"]
    assert a.tracker in a.graph.quick_thinking_llm.callbacks and a.tracker in a.graph.deep_thinking_llm.callbacks
    assert a.graph.config["holding_period_days"] == cfg["agent"]["research_horizon_days"]
    assert a.graph.config["benchmark_ticker"] == "SPY"


def test_analyze_passes_the_real_book_and_saves_the_report(analyst):
    a, state = analyst
    seen = {}

    def fake_propagate(ticker, trade_date, portfolio=None):
        seen["book"] = portfolio
        return {"company_of_interest": ticker, "trade_date": trade_date, "market_report": "Tendencia alcista.",
                "final_trade_decision": "Mantener con sesgo comprador.", "final_rating": "Overweight"}, "Overweight"

    a.graph.propagate = fake_propagate
    res = a.analyze("MU", "2026-11-16", ACCOUNT, POSITIONS)
    assert res["status"] == "ok" and res["rating"] == "Overweight"
    assert seen["book"].cash == 5_000.0 and seen["book"].position_in("MU").quantity == 30
    assert "Tendencia alcista." in (state / res["report"]).read_text()


def test_unparseable_rating_becomes_review(analyst):
    a, _ = analyst
    a.graph.propagate = lambda *args, **kw: ({"final_trade_decision": "..."}, "REVIEW")
    assert a.analyze("MU", "2026-11-16", ACCOUNT, {})["rating"] == "REVIEW"


def test_wrapped_budget_stop_is_reported_as_budget_not_error(analyst):
    a, _ = analyst

    def boom(*args, **kw):
        try:
            raise BudgetExceeded("asignación agotada")
        except BudgetExceeded as exc:
            raise RuntimeError("fallo dentro del grafo") from exc

    a.graph.propagate = boom
    assert a.analyze("MU", "2026-11-16", ACCOUNT, {})["status"] == "aborted_budget"


def test_other_failures_are_errors_and_do_not_crash_the_run(analyst):
    a, _ = analyst
    a.graph.propagate = lambda *args, **kw: (_ for _ in ()).throw(ConnectionError("sin red"))
    res = a.analyze("MU", "2026-11-16", ACCOUNT, {})
    assert res["status"] == "error" and "sin red" in res["error"] and res["rating"] is None


def test_alpaca_models_have_the_fields_the_broker_reads():
    """Si alpaca-py renombra un campo, esto falla aquí y no a media corrida."""
    from alpaca.trading.models import Asset, Calendar, Clock, Order, PortfolioHistory, Position, TradeAccount

    need = {TradeAccount: ["equity", "cash", "buying_power", "last_equity"],
            Position: ["symbol", "qty", "side", "avg_entry_price", "current_price", "market_value", "unrealized_pl"],
            Order: ["id", "status", "submitted_at", "filled_at", "symbol", "side", "type", "qty", "filled_qty",
                    "filled_avg_price", "legs", "limit_price", "stop_price", "extended_hours"],
            Asset: ["tradable", "shortable", "easy_to_borrow"],
            Calendar: ["date"], Clock: ["is_open"], PortfolioHistory: ["timestamp", "equity"]}
    for model, fields in need.items():
        missing = [f for f in fields if f not in model.model_fields]
        assert not missing, f"{model.__name__}: {missing}"


def fake_alpaca(sent, positions=None, is_open=True):
    from alpaca.trading.enums import OrderSide, OrderStatus, OrderType, PositionSide

    t = lambda d, h: datetime(2026, 11, d, h, 30, tzinfo=timezone.utc)  # noqa: E731

    def order(symbol, side, qty, px, at):
        return SimpleNamespace(submitted_at=at, filled_at=at, symbol=symbol, side=side, type=OrderType.MARKET, qty=str(qty),
                               filled_qty=str(qty), filled_avg_price=str(px), status=OrderStatus.FILLED, legs=None, id=f"o-{symbol}-{qty}",
                               limit_price=None, stop_price=None, extended_hours=False)

    pos = positions if positions is not None else [
        SimpleNamespace(symbol="MU", qty="30", side=PositionSide.LONG, avg_entry_price="300", current_price="310",
                        market_value="9300", unrealized_pl="300")]
    return SimpleNamespace(
        get_account=lambda: SimpleNamespace(equity="100000", cash="5000", buying_power="40000", last_equity="99000"),
        get_asset=lambda sym: SimpleNamespace(tradable=True, shortable=True, easy_to_borrow=True),
        get_all_positions=lambda: pos,
        get_calendar=lambda req: [SimpleNamespace(date=date(2026, 11, 16))],
        get_clock=lambda: SimpleNamespace(is_open=is_open),
        submit_order=lambda req: sent.append(req) or SimpleNamespace(id=f"id-{len(sent)}", status=OrderStatus.ACCEPTED),
        cancel_orders=lambda: [],
        get_orders=lambda req: [order("MU", OrderSide.BUY, 30, 300, t(10, 14)), order("KO", OrderSide.SELL, 5, 70, t(16, 14))],
        get_portfolio_history=lambda req: SimpleNamespace(timestamp=[1794787200], equity=[100000.0]),
    )


def test_broker_sends_market_limit_extended_and_stop_orders(monkeypatch):
    from alpaca.trading.enums import OrderSide, OrderType, TimeInForce

    monkeypatch.setenv("ALPACA_API_KEY", "k")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "s")
    broker, sent = AlpacaPaperBroker(), []
    broker.client = fake_alpaca(sent)
    assert broker.account()["equity"] == 100000.0 and broker.account()["last_equity"] == 99000.0
    assert broker.positions()["MU"]["qty"] == 30
    assert broker.is_market_day(date(2026, 11, 16)) and not broker.is_market_day(date(2026, 11, 15))
    broker.place("KO", -7)
    broker.place("MU", 5, limit_price=301.234, extended=True)
    broker.place_stop("MU", -30, 280)
    mkt, lim, stp = sent
    assert (mkt.symbol, mkt.qty, mkt.side, mkt.time_in_force, mkt.type) == ("KO", 7, OrderSide.SELL, TimeInForce.DAY, OrderType.MARKET)
    assert (lim.limit_price, lim.extended_hours, lim.time_in_force, lim.side) == (301.23, True, TimeInForce.DAY, OrderSide.BUY)
    assert (stp.stop_price, stp.time_in_force, stp.side, stp.qty) == (280, TimeInForce.GTC, OrderSide.SELL, 30)
    assert broker.asset("MU")["shortable"] is True
    assert [f["symbol"] for f in broker.fills_since(date(2026, 11, 12))] == ["KO"]
    assert broker.recent_orders()[0]["id"] == "o-MU-30"
    assert broker.equity_history()[0]["equity"] == 100000.0
