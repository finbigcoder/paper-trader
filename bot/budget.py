"""Tope de gasto real del bot.

Tres piezas:
  * ``call_cost``   convierte los tokens de una llamada en USD con la tabla de config.yaml
  * ``Ledger``      libro de gasto persistente (state/ledger.json) y asignación diaria
  * ``CostTracker`` callback de LangChain que cuenta cada llamada de TradingAgents y
                    corta la corrida (``BudgetExceeded``) al agotar la asignación

El libro es una estimación hecha con los tokens que reporta la API. El tope duro de
verdad se pone además en la consola de Anthropic (ver README).
"""
from __future__ import annotations

import json
import threading
from datetime import date
from pathlib import Path
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler

from .config import weekdays_left_in_month


class BudgetExceeded(RuntimeError):
    """La corrida alcanzó su asignación de gasto."""


# ── precio por llamada ───────────────────────────────────────
def price_row(model: str, prices: dict) -> tuple[dict, bool]:
    """Fila de precios del modelo (por prefijo más largo). Si el modelo no está en la
    tabla se cobra con la fila más cara y se marca como desconocido."""
    model = (model or "").lower()
    match = max((k for k in prices if model.startswith(k.lower())), key=len, default=None)
    if match:
        return prices[match], True
    priciest = max(prices.values(), key=lambda r: r["output"])
    return priciest, False


def call_cost(model: str, usage: dict, prices: dict) -> tuple[float, bool]:
    """USD de una llamada. ``usage`` es el ``usage_metadata`` de LangChain, donde
    ``input_tokens`` ya incluye los tokens de caché."""
    row, known = price_row(model, prices)
    inp = int(usage.get("input_tokens") or 0)
    out = int(usage.get("output_tokens") or 0)
    details = usage.get("input_token_details") or {}
    cache_read = int(details.get("cache_read") or 0)
    cache_write = int(details.get("cache_creation") or 0) + int(
        details.get("ephemeral_5m_input_tokens") or 0) + int(details.get("ephemeral_1h_input_tokens") or 0)
    plain = max(inp - cache_read - cache_write, 0)
    usd = (
        plain * row["input"]
        + cache_read * row.get("cache_read", row["input"])
        + cache_write * row.get("cache_write", row["input"])
        + out * row["output"]
    ) / 1_000_000
    threshold = row.get("long_context_threshold")
    if threshold and inp > threshold:
        usd *= row.get("long_context_multiplier", 1)
    return usd, known


# ── libro de gasto ───────────────────────────────────────────
class Ledger:
    def __init__(self, path: Path, monthly_usd: float, reserve_pct: float = 0.05,
                 first_estimate_usd: float = 0.25):
        self.path = Path(path)
        self.monthly_usd = float(monthly_usd)
        self.reserve_pct = float(reserve_pct)
        self.first_estimate_usd = float(first_estimate_usd)
        self.entries: list[dict] = []
        if self.path.exists():
            self.entries = json.loads(self.path.read_text(encoding="utf-8")).get("entries", [])

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"entries": self.entries}, indent=1), encoding="utf-8")

    def add(self, entry: dict) -> None:
        self.entries.append(entry)
        self.save()

    def spent_in_month(self, d: date) -> float:
        prefix = d.strftime("%Y-%m")
        return sum(e["usd"] for e in self.entries if e["date"].startswith(prefix))

    def spent_on(self, d: date) -> float:
        return sum(e["usd"] for e in self.entries if e["date"] == d.isoformat())

    def month_remaining(self, d: date) -> float:
        return max(self.monthly_usd - self.spent_in_month(d), 0.0)

    def run_allowance(self, d: date) -> float:
        """Lo que puede gastar la corrida de hoy: el tope mensual menos la reserva y lo
        ya gastado, repartido entre los días hábiles que quedan del mes."""
        usable = self.monthly_usd * (1 - self.reserve_pct) - self.spent_in_month(d)
        if usable <= 0:
            return 0.0
        per_day = usable / weekdays_left_in_month(d)
        return max(per_day - self.spent_on(d), 0.0)

    def estimate_kind(self, kind: str, default: float, last: int = 20) -> float:
        """Costo esperado de un tipo de gasto: promedio de los últimos ``last`` con 25% de margen."""
        xs = [e["usd"] for e in self.entries if e.get("kind") == kind and not e.get("aborted")][-last:]
        return 1.25 * sum(xs) / len(xs) if xs else float(default)

    def estimate_per_ticker(self) -> float:
        """Costo esperado del siguiente análisis: promedio de los últimos 10 completos
        con 25% de margen; antes de tener historia, ``first_estimate_usd``."""
        done = [e["usd"] for e in self.entries if e.get("ticker") and not e.get("aborted")][-10:]
        if not done:
            return self.first_estimate_usd
        return 1.25 * sum(done) / len(done)


# ── contador en vivo ─────────────────────────────────────────
class CostTracker(BaseCallbackHandler):
    """Se pasa en ``callbacks`` a TradingAgentsGraph, que lo cuelga de cada LLM. También
    cuenta las llamadas de los agentes propios del bot (triage y mesa intradía).

    Además del total, reparte el gasto por agente (el nodo de LangGraph que hizo la
    llamada), para saber con datos qué parte del pipeline se lleva el presupuesto."""

    raise_error = True  # sin esto LangChain se traga la excepción del tope

    def __init__(self, prices: dict, limit_usd: float, unknown_call_usd: float = 0.05):
        self.prices = prices
        self.limit_usd = float(limit_usd)
        self.unknown_call_usd = float(unknown_call_usd)
        self.total_usd = 0.0
        self._lock = threading.Lock()
        self._agents: dict[Any, str] = {}
        self._all_agents: dict[str, dict] = {}
        self._bucket = self._new_bucket()

    @staticmethod
    def _new_bucket() -> dict:
        return {"usd": 0.0, "calls": 0, "input_tokens": 0, "output_tokens": 0, "calls_without_usage": 0,
                "unknown_models": [], "max_prompt_tokens": 0, "by_agent": {}}

    def start_ticker(self) -> None:
        with self._lock:
            self._bucket = self._new_bucket()

    def end_ticker(self) -> dict:
        with self._lock:
            bucket, self._bucket = self._bucket, self._new_bucket()
        bucket["usd"] = round(bucket["usd"], 6)
        for a in bucket["by_agent"].values():
            a["usd"] = round(a["usd"], 6)
        return bucket

    def agent_totals(self) -> dict:
        with self._lock:
            return {k: {"usd": round(v["usd"], 6), "calls": v["calls"], "tokens": v["tokens"]} for k, v in self._all_agents.items()}

    @property
    def remaining(self) -> float:
        return self.limit_usd - self.total_usd

    def _guard(self) -> None:
        if self.total_usd >= self.limit_usd:
            raise BudgetExceeded(
                f"asignación de la corrida agotada: ${self.total_usd:.4f} de ${self.limit_usd:.4f}")

    def _remember_agent(self, run_id: Any, metadata: dict | None) -> None:
        meta = metadata or {}
        name = meta.get("agent") or meta.get("langgraph_node") or "otro"
        with self._lock:
            self._agents[run_id] = str(name)

    # Antes de cada llamada: si ya no hay asignación, no se hace.
    def on_chat_model_start(self, serialized: Any, messages: Any, *, run_id: Any = None,
                            metadata: dict | None = None, **kwargs: Any) -> None:
        self._guard()
        self._remember_agent(run_id, metadata)

    def on_llm_start(self, serialized: Any, prompts: Any, *, run_id: Any = None,
                     metadata: dict | None = None, **kwargs: Any) -> None:
        self._guard()
        self._remember_agent(run_id, metadata)

    def on_llm_error(self, error: BaseException, *, run_id: Any = None, **kwargs: Any) -> None:
        with self._lock:
            self._agents.pop(run_id, None)

    def on_llm_end(self, response: Any, *, run_id: Any = None, **kwargs: Any) -> None:
        with self._lock:
            agent = self._agents.pop(run_id, "otro")
        found = False
        for generations in getattr(response, "generations", None) or []:
            for gen in generations:
                msg = getattr(gen, "message", None)
                usage = getattr(msg, "usage_metadata", None)
                if not usage:
                    continue
                meta = getattr(msg, "response_metadata", None) or {}
                model = meta.get("model_name") or meta.get("model") or ""
                usd, known = call_cost(model, dict(usage), self.prices)
                self._record(usd, usage, None if known else model, agent)
                found = True
        if not found:
            self._record(self.unknown_call_usd, {}, None, agent, counted=False)

    def _record(self, usd: float, usage: dict, unknown_model: str | None, agent: str = "otro",
                counted: bool = True) -> None:
        inp, out = int(usage.get("input_tokens") or 0), int(usage.get("output_tokens") or 0)
        with self._lock:
            b = self._bucket
            b["usd"] += usd
            b["calls"] += 1
            b["input_tokens"] += inp
            b["output_tokens"] += out
            b["max_prompt_tokens"] = max(b["max_prompt_tokens"], inp)
            if not counted:
                b["calls_without_usage"] += 1
            if unknown_model is not None and unknown_model not in b["unknown_models"]:
                b["unknown_models"].append(unknown_model)
            a = b["by_agent"].setdefault(agent, {"usd": 0.0, "calls": 0, "tokens": 0})
            a["usd"] += usd
            a["calls"] += 1
            a["tokens"] += inp + out
            g = self._all_agents.setdefault(agent, {"usd": 0.0, "calls": 0, "tokens": 0})
            g["usd"] += usd
            g["calls"] += 1
            g["tokens"] += inp + out
            self.total_usd += usd
