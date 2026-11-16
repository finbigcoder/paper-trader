"""Un despertar del agente trader.

GitHub Actions lo corre cada 30 minutos de 4:00 a 20:00 (hora de Nueva York), de lunes a
viernes. El primer despertar del día además prepara el día (OpenBB + Qlib) y pone al
corriente la bitácora.

    python -m bot.tick              despertar real (cuenta paper)
    python -m bot.tick --dry-run    el agente decide, pero sus órdenes no se envían
    python -m bot.tick --force      corre aunque sea feriado o fuera de horario
    python -m bot.tick --demo       demo sin llaves ni LLM (escribe en state_demo/)
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
import warnings
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from .budget import CostTracker, Ledger
from .config import NY, ROOT, load_config, state_dir
from .data import last_closes
from .journal import backfill_research, record_fills, update_journal, update_virtual
from .market import Intraday, StaticIntraday, prepare_day
from .session import is_last_tick, now_et, session_of, ticks_left
from .state import load_json, now_iso, save_json, write_benchmark, write_snapshot
from .trader import Desk, run_agent

REQUIRED_ENV = ("ALPACA_API_KEY", "ALPACA_SECRET_KEY", "ANTHROPIC_API_KEY")


def log(msg: str) -> None:
    print(f"[bot] {msg}", flush=True)


def day_path(sd: Path, d: date) -> Path:
    return sd / "days" / f"{d.isoformat()}.json"


def housekeeping(sd: Path, broker, prices: pd.DataFrame, cfg: dict, today: date) -> list[str]:
    """Pone al corriente bitácora, regla de referencia y resultado de investigaciones viejas."""
    notes = []
    try:
        record_fills(sd, broker.fills_since(today - timedelta(days=10)))
        update_journal(sd)
    except Exception as exc:
        notes.append(f"no se pudo actualizar la bitácora: {type(exc).__name__}: {exc}"[:200])
    try:
        update_virtual(sd, prices, cfg["benchmark"])
        backfill_research(sd, prices, cfg["benchmark"], int(cfg["agent"]["research_horizon_days"]))
        write_benchmark(sd, prices, cfg["benchmark"])
    except Exception as exc:
        notes.append(f"no se pudo calcular la atribución: {type(exc).__name__}: {exc}"[:200])
    return notes


def run_tick(*, cfg: dict, sd: Path, broker, now: datetime, prep: dict, intraday, make_llm, make_analyst,
             dry_run: bool) -> dict:
    """Un despertar completo: presupuesto, foto de la mesa, agente, registro."""
    today = now.date()
    day = load_json(day_path(sd, today), {"date": today.isoformat(), "prep": prep, "ticks": []})
    day["prep"] = prep
    session = session_of(now)
    agent_cfg, b = cfg["agent"], cfg["budget"]

    ledger = Ledger(sd / "ledger.json", b["monthly_usd"], b.get("reserve_pct", 0.05), b.get("first_estimate_usd", 0.25))
    left = ticks_left(now, agent_cfg)
    last = is_last_tick(now, agent_cfg)
    est_tick = ledger.estimate_kind("tick", b.get("first_tick_usd", 0.01))
    est_research = ledger.estimate_kind("research", b.get("first_estimate_usd", 0.25))
    allowance = ledger.run_allowance(today)
    limit = max(allowance - est_tick * (left - 1), 0.0)          # deja con qué pagar los despertares que faltan
    tracker = CostTracker(cfg["prices"], limit, b.get("unknown_call_usd", 0.05))
    tick = {"at": now.isoformat(timespec="seconds"), "time": f"{now:%H:%M}", "session": session, "last": last,
            "budget": {"allowance_today": round(allowance, 4), "limit": round(limit, 4), "ticks_left": left,
                       "est_tick": round(est_tick, 4), "est_research": round(est_research, 4)}}

    symbols = list(dict.fromkeys(list(broker.positions()) + [r["symbol"] for r in prep["ranking"][: int(agent_cfg["watchlist_momentum"])]]
                                 + [e["symbol"] for e in prep.get("earnings", [])] + cfg["universe"] + [cfg["benchmark"], "QQQ"]))
    try:
        intraday.load(symbols)
    except Exception as exc:
        tick.setdefault("warnings", []).append(f"no se pudieron leer precios de hoy: {type(exc).__name__}: {exc}"[:200])

    desk = Desk(cfg=cfg, sd=sd, broker=broker, intraday=intraday, prep=prep, now=now, session=session, tracker=tracker,
                make_analyst=make_analyst, ledger=ledger, est_research=est_research, last_tick=last, ticks_left=left,
                dry_run=dry_run, day=day)
    if limit < est_tick * 0.5:
        tick.update(status="skipped_budget", final=None,
                    error=f"sin presupuesto para pensar: quedan ${limit:.3f} para este despertar y uno cuesta ~${est_tick:.3f}")
        log(tick["error"])
    else:
        log(f"{now:%H:%M} {session}: el agente piensa (puede gastar ${limit:.3f})")
        res = run_agent(desk, make_llm(tracker, desk))
        tick.update(status=res["status"], final=res["final"], steps=res["steps"], error=res["error"])
    research_usd = sum(r["usd"] for r in desk.research_done)
    ledger.add({"date": today.isoformat(), "ticker": None, "kind": "tick", "usd": round(tracker.total_usd - research_usd, 6),
                "aborted": tick["status"] not in ("ok", "max_steps")})
    tick.update(tools=desk.log, orders=desk.orders, notes=desk.notes, research=desk.research_done,
                cost={"usd": round(tracker.total_usd, 6), "research_usd": round(research_usd, 6)},
                account={k: round(v, 2) for k, v in broker.account().items() if v is not None}, positions=len(broker.positions()))
    tick["cost"]["by_agent"] = tracker.agent_totals()
    day["ticks"].append(tick)
    day["spent_usd"] = round(sum(t["cost"]["usd"] for t in day["ticks"]), 6)
    save_json(day_path(sd, today), day)
    write_snapshot(sd, broker, now.isoformat(timespec="seconds"))
    status = load_json(sd / "status.json", {})
    status.update(setup="complete", last_tick=tick["at"], updated_at=now_iso())
    save_json(sd / "status.json", status)
    log(f"listo: {len(desk.orders)} órdenes, {len(desk.research_done)} investigaciones, ${tracker.total_usd:.4f}")
    return tick


def real_tick(args) -> int:
    from .agents import Analyst
    from .broker import AlpacaPaperBroker
    from .trader import make_trader_llm

    cfg, sd, now = load_config(), state_dir(), now_et()
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        save_json(sd / "status.json", {"setup": "incomplete", "missing": missing, "updated_at": now_iso()})
        log(f"configuración incompleta, faltan: {', '.join(missing)}. No se hizo nada.")
        return 0
    broker = AlpacaPaperBroker()
    session = session_of(now)
    if not args.force:
        if not broker.is_market_day(now.date()):
            log(f"{now.date()}: el mercado no abre hoy.")
            return 0
        if session == "closed":
            log(f"{now:%H:%M}: fuera de horario.")
            return 0
    dry = args.dry_run or cfg["mode"] == "dry_run"
    with tempfile.TemporaryDirectory(prefix="bot_work_") as tmp:
        work = Path(tmp)
        day = load_json(day_path(sd, now.date()), {})
        prep = day.get("prep")
        prices = None
        if not prep:
            log("primer despertar del día: OpenBB + Qlib")
            prep, prices = prepare_day(cfg, sd, now.date(), work, list(broker.positions()))
            prep["warnings"] = prep.get("warnings", []) + housekeeping(sd, broker, prices, cfg, now.date())
        prev = {s: x["close"] for s, x in prep["stats"].items()}
        run_tick(cfg=cfg, sd=sd, broker=broker, now=now, prep=prep, intraday=Intraday(prev),
                 make_llm=lambda tracker, desk: make_trader_llm(cfg, tracker),
                 make_analyst=lambda tracker: Analyst(cfg, sd, work, tracker), dry_run=dry)
    return 0


DEMO_TIMES = [(4, 8), (9, 38), (12, 8), (15, 38), (19, 38)]


def demo_prices_at(bar, hm: tuple[int, int], prev_close: float) -> float:
    o, h, l, c = bar
    if hm < (9, 30):
        return prev_close + 0.5 * (o - prev_close)
    if hm < (11, 0):
        return o
    if hm < (15, 0):
        return l if c < o else h           # a media sesión el día ya marcó su extremo
    return c


def demo(args) -> int:
    """Simula ``--days`` días con precios reales de OpenBB, cuenta falsa y un agente con
    reglas fijas en lugar del LLM. Sirve para ver el dashboard; no dice nada del agente real."""
    from .agents import DemoAnalyst
    from .broker import FakeBroker
    from .data import fetch_prices
    from .trader import ScriptedTrader

    cfg = load_config()
    sd = state_dir(os.environ.get("BOT_STATE_DIR") or ROOT / "state_demo")
    for name in ("ledger.json", "fake_account.json", "journal.json", "fills.json", "book.json", "virtual.json", "research.json"):
        (sd / name).unlink(missing_ok=True)
    for folder in ("days", "agent"):
        for f in (sd / folder).glob("*"):
            f.unlink()
    today = now_et().date()
    prices, meta = fetch_prices(cfg["universe"] + [cfg["benchmark"]], cfg["data"]["history_start"], cfg["data"]["providers"], today)
    days = [d.date() for d in sorted(prices["date"].unique())[-args.days:]]
    broker = FakeBroker(sd / "fake_account.json")
    em = {"provider": "OpenBB (Nasdaq)", "ok": True, "found": 0, "note": "la demo no consulta el calendario"}
    with tempfile.TemporaryDirectory(prefix="bot_demo_") as tmp:
        for i, d in enumerate(days):
            asof = prices[prices["date"] < pd.Timestamp(d)]
            last = asof["date"].max().strftime("%Y-%m-%d")
            prep, _ = prepare_day(cfg, sd, d, Path(tmp) / str(i), list(broker.positions()), use_qlib=(i == len(days) - 1),
                                  prices=asof, data_meta={**meta, "last_date": last, "stale": False, "expected_last_date": last},
                                  earnings=([], em))
            prev = last_closes(asof)
            bars = {r.symbol: (r.open, r.high, r.low, r.close) for r in prices[prices["date"] == pd.Timestamp(d)].itertuples()}
            for hm in DEMO_TIMES:
                now = datetime(d.year, d.month, d.day, *hm, tzinfo=NY)
                px = {s: demo_prices_at(bars[s], hm, prev.get(s, bars[s][0])) for s in bars}
                broker.set_market(px, session_of(now), now.isoformat(timespec="seconds"))
                run_tick(cfg=cfg, sd=sd, broker=broker, now=now, prep=prep, intraday=StaticIntraday(prev, px),
                         make_llm=lambda tracker, desk: ScriptedTrader(desk, tracker, cfg["llm"]["trader_model"]),
                         make_analyst=lambda tracker: DemoAnalyst(cfg, sd, tracker), dry_run=False)
            broker.close_day(d)
        record_fills(sd, broker.fills_since(days[0]))
        housekeeping(sd, broker, prices, cfg, days[-1] + timedelta(days=1))
        write_snapshot(sd, broker, f"{days[-1].isoformat()}T20:15:00-05:00")
    save_json(sd / "status.json", {"setup": "demo", "updated_at": now_iso()})
    log(f"demo escrita en {sd} ({len(days)} días, {len(days) * len(DEMO_TIMES)} despertares)")
    return 0


def main(argv=None) -> int:
    warnings.filterwarnings("ignore", category=FutureWarning)
    os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--days", type=int, default=20, help="días simulados en --demo")
    args = p.parse_args(argv)
    return demo(args) if args.demo else real_tick(args)


if __name__ == "__main__":
    sys.exit(main())
