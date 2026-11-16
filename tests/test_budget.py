from datetime import date, timedelta

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from bot.budget import BudgetExceeded, CostTracker, Ledger, call_cost
from bot.config import load_config

PRICES = load_config()["prices"]


def test_haiku_cost_and_long_context_tier():
    usd, known = call_cost("claude-haiku-5-5", {"input_tokens": 50_000, "output_tokens": 2_000}, PRICES)
    assert known and usd == pytest.approx(50_000 * 0.10 / 1e6 + 2_000 * 0.50 / 1e6)
    big, _ = call_cost("claude-haiku-5-5", {"input_tokens": 150_000, "output_tokens": 2_000}, PRICES)
    assert big == pytest.approx(5 * (150_000 * 0.10 / 1e6 + 2_000 * 0.50 / 1e6))


def test_dated_model_name_matches_by_prefix():
    usd, known = call_cost("claude-sonnet-5-5-20260928", {"input_tokens": 1_000_000, "output_tokens": 0}, PRICES)
    assert known and usd == pytest.approx(2.0)


def test_unknown_model_is_charged_at_priciest_rate():
    usd, known = call_cost("modelo-raro", {"input_tokens": 1_000_000, "output_tokens": 1_000_000}, PRICES)
    assert not known and usd == pytest.approx(4.0 + 20.0)


def test_cached_tokens_are_not_double_counted():
    usage = {"input_tokens": 10_000, "output_tokens": 0, "input_token_details": {"cache_read": 8_000}}
    usd, _ = call_cost("claude-sonnet-5-5", usage, PRICES)
    assert usd == pytest.approx((2_000 * 2.0 + 8_000 * 0.10) / 1e6)


def test_allowance_spreads_remaining_budget_over_remaining_weekdays(tmp_path):
    ledger = Ledger(tmp_path / "l.json", monthly_usd=20, reserve_pct=0.05)
    d = date(2026, 11, 16)  # lunes; quedan 11 días hábiles en noviembre
    assert ledger.run_allowance(d) == pytest.approx(19 / 11)
    ledger.add({"date": d.isoformat(), "ticker": "AAPL", "usd": 1.0})
    assert ledger.run_allowance(d) == pytest.approx(18 / 11 - 1.0)
    assert ledger.run_allowance(date(2026, 12, 1)) == pytest.approx(19 / 23)  # mes nuevo, tope nuevo


def test_allowance_is_zero_once_cap_is_spent(tmp_path):
    ledger = Ledger(tmp_path / "l.json", monthly_usd=5)
    ledger.add({"date": "2026-11-16", "ticker": "AAPL", "usd": 4.9})
    assert ledger.run_allowance(date(2026, 11, 17)) == 0.0


def test_ledger_persists(tmp_path):
    Ledger(tmp_path / "l.json", 20).add({"date": "2026-11-16", "ticker": "X", "usd": 0.5})
    assert Ledger(tmp_path / "l.json", 20).spent_in_month(date(2026, 11, 30)) == 0.5


def _message(inp, out, model="claude-haiku-5-5"):
    return AIMessage(content="ok", usage_metadata={"input_tokens": inp, "output_tokens": out, "total_tokens": inp + out},
                     response_metadata={"model_name": model})


def test_tracker_counts_real_langchain_calls_and_blocks_the_next_one():
    """Pasa por la maquinaria real de callbacks de LangChain, como hace TradingAgents."""
    tracker = CostTracker(PRICES, limit_usd=0.015)
    llm = GenericFakeChatModel(messages=iter([_message(90_000, 2_000) for _ in range(5)]), callbacks=[tracker])
    llm.invoke("uno")   # $0.010
    llm.invoke("dos")   # $0.020 → ya pasó la asignación
    assert tracker.total_usd == pytest.approx(0.02)
    with pytest.raises(BudgetExceeded):
        llm.invoke("tres")  # se bloquea antes de llamar
    assert tracker.total_usd == pytest.approx(0.02)
    bucket = tracker.end_ticker()
    assert bucket["calls"] == 2 and bucket["input_tokens"] == 180_000


def test_budget_stop_propagates_out_of_a_langgraph_run():
    from langgraph.graph import END, START, StateGraph

    tracker = CostTracker(PRICES, limit_usd=0.005)
    llm = GenericFakeChatModel(messages=iter([_message(90_000, 2_000) for _ in range(5)]), callbacks=[tracker])
    graph = StateGraph(dict)
    graph.add_node("a", lambda s: {"x": llm.invoke("a").content})
    graph.add_node("b", lambda s: {"x": llm.invoke("b").content})
    graph.add_edge(START, "a")
    graph.add_edge("a", "b")
    graph.add_edge("b", END)
    with pytest.raises(Exception) as err:
        graph.compile().invoke({})
    cause, found = err.value, False
    while cause is not None:
        found = found or isinstance(cause, BudgetExceeded)
        cause = cause.__cause__ or cause.__context__
    assert found


def test_call_without_usage_is_charged_a_fixed_estimate():
    tracker = CostTracker(PRICES, limit_usd=1.0, unknown_call_usd=0.05)
    llm = GenericFakeChatModel(messages=iter([AIMessage(content="sin uso")]), callbacks=[tracker])
    llm.invoke("x")
    assert tracker.total_usd == pytest.approx(0.05)
    assert tracker.end_ticker()["calls_without_usage"] == 1


def test_a_simulated_month_never_exceeds_the_cap(tmp_path):
    """21 días hábiles con análisis caros: el gasto del mes queda bajo el tope."""
    cap = 20.0
    ledger = Ledger(tmp_path / "l.json", monthly_usd=cap, first_estimate_usd=0.25)
    d = date(2026, 12, 1)
    while d.month == 12:
        if d.weekday() < 5:
            tracker = CostTracker(PRICES, ledger.run_allowance(d))
            for ticker in range(8):
                if tracker.remaining < ledger.estimate_per_ticker():
                    break
                tracker.start_ticker()
                aborted = False
                try:
                    for _ in range(20):  # 20 llamadas de Sonnet de ~$0.05 = ~$1 por ticker
                        tracker.on_chat_model_start({}, [])
                        usd, _ = call_cost("claude-sonnet-5-5", {"input_tokens": 20_000, "output_tokens": 1_000}, PRICES)
                        tracker._record(usd, {"input_tokens": 20_000, "output_tokens": 1_000}, None)
                except BudgetExceeded:
                    aborted = True
                ledger.add({"date": d.isoformat(), "ticker": str(ticker), "usd": tracker.end_ticker()["usd"], "aborted": aborted})
        d += timedelta(days=1)
    spent = ledger.spent_in_month(date(2026, 12, 31))
    assert 0 < spent <= cap


def test_cost_is_split_by_langgraph_node():
    """TradingAgents corre en LangGraph: el nombre del nodo dice qué agente gastó."""
    from langgraph.graph import END, START, StateGraph

    tracker = CostTracker(PRICES, limit_usd=1.0)
    llm = GenericFakeChatModel(messages=iter([_message(10_000, 500) for _ in range(3)]), callbacks=[tracker])
    graph = StateGraph(dict)
    graph.add_node("News Analyst", lambda s: {"x": llm.invoke("a").content + llm.invoke("b").content})
    graph.add_node("Trader", lambda s: {"x": llm.invoke("c").content})
    graph.add_edge(START, "News Analyst")
    graph.add_edge("News Analyst", "Trader")
    graph.add_edge("Trader", END)
    graph.compile().invoke({})
    by = tracker.end_ticker()["by_agent"]
    assert by["News Analyst"]["calls"] == 2 and by["Trader"]["calls"] == 1
    assert by["News Analyst"]["usd"] == pytest.approx(2 * by["Trader"]["usd"])
