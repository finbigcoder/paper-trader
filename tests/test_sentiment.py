"""Sentimiento de respaldo (ApeWisdom), sin red."""
from bot import sentiment

ROWS = [{"rank": 4, "ticker": "MU", "name": "Micron Technology", "mentions": 108, "upvotes": 243, "rank_24h_ago": 15, "mentions_24h_ago": 15}]


def test_block_reports_rank_mentions_and_change(monkeypatch):
    monkeypatch.setattr(sentiment, "_page", lambda page, timeout: (ROWS, 1))
    out = sentiment.reddit_attention("mu")
    assert "$MU (Micron Technology): puesto #4" in out and "108 menciones (ayer 15, cambio +620%)" in out and "243 votos" in out
    assert "no aparece entre los 1 tickers" in sentiment.reddit_attention("KO")


def test_network_failure_becomes_a_placeholder(monkeypatch):
    def boom(page, timeout):
        raise OSError("sin red")

    monkeypatch.setattr(sentiment, "_page", boom)
    assert sentiment.reddit_attention("MU").startswith("<Reddit/ApeWisdom no disponible: OSError")


def test_fallback_only_replaces_a_failed_reddit_fetch(monkeypatch):
    from tradingagents.agents.analysts import sentiment_analyst as sa

    monkeypatch.setattr(sentiment, "_page", lambda page, timeout: (ROWS, 1))
    monkeypatch.setattr(sa, "fetch_reddit_posts", lambda ticker, *a, **k: "<Reddit unavailable: fetch failed (r/stocks)>" if ticker == "MU" else "posts reales")
    sentiment.install()
    assert "puesto #4" in sa.fetch_reddit_posts("MU", ("stocks",), start_date="2026-11-09", end_date="2026-11-16")
    assert sa.fetch_reddit_posts("KO") == "posts reales"
