"""Reloj del agente: en qué sesión está el mercado y cuántos despertares quedan hoy."""
from __future__ import annotations

import math
from datetime import datetime, time

from .config import NY

PRE_OPEN, REG_OPEN, REG_CLOSE, POST_CLOSE = time(4, 0), time(9, 30), time(16, 0), time(20, 0)
NAMES = {"pre": "pre-market", "regular": "horario regular", "post": "post-market", "closed": "mercado cerrado"}


def now_et() -> datetime:
    return datetime.now(NY)


def session_of(t: datetime) -> str:
    """'pre', 'regular', 'post' o 'closed' (no sabe de feriados: eso lo dice el broker)."""
    t = t.astimezone(NY)
    if t.weekday() >= 5:
        return "closed"
    hm = t.time()
    if PRE_OPEN <= hm < REG_OPEN:
        return "pre"
    if REG_OPEN <= hm < REG_CLOSE:
        return "regular"
    if REG_CLOSE <= hm < POST_CLOSE:
        return "post"
    return "closed"


def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def ticks_left(t: datetime, agent_cfg: dict) -> int:
    """Despertares que quedan hoy contando el actual (mínimo 1)."""
    t = t.astimezone(NY)
    now = t.hour * 60 + t.minute
    end = _minutes(agent_cfg.get("session_end", "20:00"))
    return max(1, math.ceil((end - now) / int(agent_cfg["tick_minutes"])))


def is_last_tick(t: datetime, agent_cfg: dict) -> bool:
    return ticks_left(t, agent_cfg) <= 1
