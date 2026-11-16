"""El equipo de research del agente: TradingAgents.

El agente trader lo llama con su herramienta ``research`` cuando quiere una opinión a
fondo sobre una acción: analistas de mercado, sentimiento, noticias y fundamentales, debate
alcista contra bajista, trader, equipo de riesgo y portfolio manager. Devuelve
Buy / Overweight / Hold / Underweight / Sell con horizonte de semanas. Cuesta ~15-20
llamadas al LLM y tarda minutos, por eso el agente decide cuándo vale la pena.
"""
from __future__ import annotations

import copy
import re
import shutil
import tempfile
import time
import warnings
from datetime import date, timedelta
from pathlib import Path

from .budget import BudgetExceeded, CostTracker

RATINGS = ("Buy", "Overweight", "Hold", "Underweight", "Sell")


def headlines_from_news(news_text: str, limit: int) -> list[str]:
    """Solo los titulares (líneas '### ') del texto de noticias de TradingAgents."""
    heads = [re.sub(r"\s+", " ", ln[4:]).strip()[:180] for ln in str(news_text).splitlines() if ln.startswith("### ")]
    return heads[:limit]


def is_budget_stop(exc: BaseException) -> BudgetExceeded | None:
    """LangGraph puede envolver la excepción del tope; se reconoce por la causa."""
    cause: BaseException | None = exc
    while cause is not None:
        if isinstance(cause, BudgetExceeded):
            return cause
        cause = cause.__cause__ or cause.__context__
    return None


class Analyst:
    def __init__(self, cfg: dict, state: Path, workdir: Path, tracker: CostTracker):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from tradingagents.default_config import DEFAULT_CONFIG
            from tradingagents.graph.trading_graph import TradingAgentsGraph

        llm = cfg["llm"]
        ta_cfg = copy.deepcopy(DEFAULT_CONFIG)
        ta_cfg.update({
            "llm_provider": llm["provider"], "quick_think_llm": llm["quick_model"], "deep_think_llm": llm["deep_model"],
            "max_debate_rounds": int(llm.get("max_debate_rounds", 1)), "max_risk_discuss_rounds": int(llm.get("max_risk_rounds", 1)),
            "llm_max_retries": 4, "results_dir": str(workdir / "ta_logs"), "data_cache_dir": str(workdir / "ta_cache"),
            # Memoria de TradingAgents, persistente en state/: evalúa cada decisión pasada
            # después de N días y escribe una lección.
            "memory_log_path": str(state / "memory" / "trading_memory.md"),
            "holding_period_days": int(cfg["agent"]["research_horizon_days"]),
            "benchmark_ticker": cfg["benchmark"],
        })
        (state / "memory").mkdir(parents=True, exist_ok=True)
        self.cfg, self.tracker, self.state, self.ta_cfg = cfg, tracker, state, ta_cfg
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # el modelo puede no estar en el catálogo de TradingAgents
            self.graph = TradingAgentsGraph(selected_analysts=tuple(llm["analysts"]), debug=False, config=ta_cfg, callbacks=[tracker])

    def headlines(self, symbol: str, today: date, limit: int = 8) -> list[str]:
        """Titulares recientes con la misma herramienta de noticias que usa TradingAgents."""
        from tradingagents.dataflows.config import set_config
        from tradingagents.dataflows.router import route_to_vendor

        set_config(self.ta_cfg)
        text = route_to_vendor("get_news", symbol, (today - timedelta(days=4)).isoformat(), today.isoformat())
        return headlines_from_news(text, limit)

    def analyze(self, symbol: str, trade_date: str, account: dict, positions: dict[str, dict]) -> dict:
        from tradingagents.agents.rating import is_review
        from tradingagents.portfolio import PortfolioContext, Position
        from tradingagents.reporting import write_report_tree

        book = PortfolioContext(cash=account["cash"], currency="USD", positions=[
            Position(ticker=s, quantity=p["qty"], average_price=p.get("avg_price")) for s, p in positions.items()])
        self.tracker.start_ticker()
        started = time.time()
        result = {"symbol": symbol, "rating": None, "status": "ok", "error": None, "report": None, "summary": None}
        try:
            final_state, rating = self.graph.propagate(symbol, trade_date, portfolio=book)
            result["rating"] = "REVIEW" if is_review(rating) else str(rating)
            result["summary"] = (final_state.get("final_trade_decision") or "")[:1800]
            tmp = Path(tempfile.mkdtemp(prefix="ta_report_"))
            try:
                md = write_report_tree(final_state, symbol, tmp, settings=self.graph.run_settings(), html=False)
                dest = self.state / "reports" / trade_date / f"{symbol}.md"
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(md, dest)
                result["report"] = f"reports/{trade_date}/{symbol}.md"
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
        except Exception as exc:
            stop = is_budget_stop(exc)
            result.update(status="aborted_budget" if stop else "error", error=str(stop) if stop else f"{type(exc).__name__}: {exc}"[:500])
        result["seconds"] = round(time.time() - started, 1)
        result["cost"] = self.tracker.end_ticker()
        return result


class DemoAnalyst:
    """Para la demo y los tests: calificación aleatoria y tokens simulados. Nunca se usa en real."""

    AGENTS = ["Market Analyst", "Sentiment Analyst", "News Analyst", "Fundamentals Analyst", "Bull Researcher",
              "Bear Researcher", "Research Manager", "Trader", "Aggressive Analyst", "Conservative Analyst",
              "Neutral Analyst", "Portfolio Manager"]

    def __init__(self, cfg: dict, state: Path, tracker: CostTracker, seed: int = 0):
        self.cfg, self.state, self.tracker, self.seed = cfg, state, tracker, seed

    def headlines(self, symbol: str, today: date, limit: int = 8) -> list[str]:
        return [f"[DEMO] Titular de ejemplo sobre {symbol}", f"[DEMO] Analistas revisan su precio objetivo de {symbol}"][:limit]

    def analyze(self, symbol: str, trade_date: str, account: dict, positions: dict[str, dict]) -> dict:
        import random

        from .trader import simulate_call

        rng = random.Random(f"{symbol}-{trade_date}-{self.seed}")
        self.tracker.start_ticker()
        result = {"symbol": symbol, "rating": None, "status": "ok", "error": None, "report": None, "summary": None}
        try:
            for agent in self.AGENTS:
                simulate_call(self.tracker, self.cfg["llm"]["quick_model"], agent, rng.randint(4000, 30000), rng.randint(400, 2200))
            rating = rng.choices(RATINGS, weights=(3, 3, 3, 1.5, 1))[0]
            result.update(rating=rating, summary=f"[DEMO · sin LLM] Calificación simulada {rating} para {symbol}.")
            dest = self.state / "reports" / trade_date / f"{symbol}.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(f"# {symbol}, {trade_date}\n\n> **DEMO**: reporte de ejemplo generado sin LLM.\n\n## Decisión\n\n**{rating}**\n",
                            encoding="utf-8")
            result["report"] = f"reports/{trade_date}/{symbol}.md"
        except BudgetExceeded as exc:
            result.update(status="aborted_budget", error=str(exc))
        result["seconds"] = round(rng.uniform(60, 240), 1)
        result["cost"] = self.tracker.end_ticker()
        return result
