"""Sentimiento de Reddit vía ApeWisdom cuando Reddit bloquea la consulta directa.

Reddit responde 403 a los servidores de GitHub. ApeWisdom (apewisdom.io) publica gratis y
sin llave cuántas veces se menciona cada ticker en los foros de acciones de Reddit, sus votos
y cómo cambió contra ayer. No trae el texto de las publicaciones: es atención, no opinión.
"""
from __future__ import annotations

import html
import json
from urllib.request import Request, urlopen

API = "https://apewisdom.io/api/v1.0/filter/all-stocks/page/{page}"
_cache: dict[int, list] = {}


def _page(page: int, timeout: float) -> tuple[list, int]:
    if page not in _cache:
        req = Request(API.format(page=page), headers={"User-Agent": "paper-trader-bot", "Accept": "application/json"})
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        _cache[page] = [data.get("results") or [], int(data.get("pages") or 1)]
    return _cache[page][0], _cache[page][1]


def reddit_attention(ticker: str, max_pages: int = 3, timeout: float = 10.0) -> str:
    """Bloque de texto para el analista de sentimiento. Nunca lanza excepciones."""
    t = ticker.strip().upper()
    head = "Reddit (vía ApeWisdom: conteo de menciones en foros de acciones, últimas 24 h; sin texto de publicaciones)"
    try:
        seen, pages = 0, 1
        for page in range(1, max_pages + 1):
            rows, pages = _page(page, timeout)
            seen += len(rows)
            for r in rows:
                if str(r.get("ticker", "")).upper() == t:
                    m, m0 = int(r.get("mentions") or 0), int(r.get("mentions_24h_ago") or 0)
                    chg = f"{(m - m0) / m0 * 100:+.0f}%" if m0 else "sin dato de ayer"
                    return (f"{head}\n${t} ({html.unescape(str(r.get('name', '')))}): puesto #{r.get('rank')} en menciones "
                            f"(ayer #{r.get('rank_24h_ago')}), {m} menciones (ayer {m0}, cambio {chg}), {r.get('upvotes')} votos.\n"
                            "Mide atención, no dirección: muchas menciones no dicen si la opinión es alcista o bajista.")
            if page >= pages:
                break
        return f"{head}\n${t} no aparece entre los {seen} tickers más mencionados: poca atención minorista en Reddit."
    except Exception as exc:                                    # red, JSON, lo que sea
        return f"<Reddit/ApeWisdom no disponible: {type(exc).__name__}; esto no es ausencia de discusión>"


def install() -> None:
    """Si la consulta directa a Reddit falla, el analista de sentimiento recibe ApeWisdom."""
    from tradingagents.agents.analysts import sentiment_analyst as sa

    if getattr(sa.fetch_reddit_posts, "_with_fallback", False):
        return
    original = sa.fetch_reddit_posts

    def fetch(ticker, *args, **kwargs):
        block = original(ticker, *args, **kwargs)
        return reddit_attention(ticker) if str(block).startswith("<Reddit unavailable") else block

    fetch._with_fallback = True
    sa.fetch_reddit_posts = fetch
