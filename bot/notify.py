"""Correo después de cada despertar: cuándo empezó, cuándo terminó y cuánto costó.

Solo usa la librería estándar, así corre aunque falle la instalación del bot.

    python3 -m bot.notify start     imprime INICIO y gasto acumulado (para $GITHUB_ENV)
    python3 -m bot.notify send      arma y manda el correo

Variables (en GitHub Actions):
    GMAIL_USER, GMAIL_APP_PASSWORD  cuenta que envía (secrets; contraseña de aplicación de Google)
    EMAIL_TO                        destinatario (secret opcional; si falta, GMAIL_USER)
    BOT_START, BOT_LEDGER_BEFORE    los escribe "start"
    BOT_RESULT_PATH                 resultado que deja bot.tick
    JOB_STATUS, RUN_URL, PAGES_URL  los pone el workflow
Sin GMAIL_USER o GMAIL_APP_PASSWORD no manda nada y no falla.
"""
from __future__ import annotations

import json
import os
import re
import smtplib
import ssl
import sys
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
NY = ZoneInfo("America/New_York")
SES = {"pre": "pre-market", "regular": "horario regular", "post": "post-market", "closed": "mercado cerrado"}
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
STATUS = {"ok": "pensó y terminó", "max_steps": "pensó hasta el máximo de vueltas", "skipped_budget": "no pensó: sin presupuesto",
          "aborted_budget": "se cortó por el tope de gasto", "error": "error del agente"}
OUTCOME = {"setup_incomplete": "No operó: faltan llaves", "market_holiday": "No operó: el mercado no abre hoy",
           "closed": "No operó: fuera de horario"}


def state_dir() -> Path:
    return Path(os.environ.get("BOT_STATE_DIR") or ROOT / "state")


def ledger_total(sd: Path) -> float:
    try:
        entries = json.loads((sd / "ledger.json").read_text(encoding="utf-8")).get("entries", [])
    except (OSError, ValueError):
        return 0.0
    return sum(float(e.get("usd") or 0) for e in entries)


def month_spent(sd: Path, month: str) -> float:
    try:
        entries = json.loads((sd / "ledger.json").read_text(encoding="utf-8")).get("entries", [])
    except (OSError, ValueError):
        return 0.0
    return sum(float(e.get("usd") or 0) for e in entries if str(e.get("date", "")).startswith(month))


def monthly_cap() -> float | None:
    try:
        m = re.search(r"^\s*monthly_usd:\s*([0-9.]+)", (ROOT / "config.yaml").read_text(encoding="utf-8"), re.M)
        return float(m.group(1)) if m else None
    except OSError:
        return None


def usd(x: float, d: int = 4) -> str:
    return f"${x:,.{d}f}"


def fmt_ny(t: datetime) -> str:
    n = t.astimezone(NY)
    return f"{n:%H:%M:%S} hora de Nueva York ({t.astimezone(timezone.utc):%H:%M} UTC)"


def build(start: datetime, end: datetime, spent: float, result: dict | None, job_status: str, sd: Path,
          run_url: str = "", pages_url: str = "") -> tuple[str, str]:
    """(asunto, cuerpo). ``spent`` es lo que subió el registro de gasto durante este despertar."""
    ny = start.astimezone(NY)
    secs = max(int((end - start).total_seconds()), 0)
    month = ny.strftime("%Y-%m")
    cap = monthly_cap()
    r = result or {}
    orders = [o for o in r.get("orders") or [] if not str(o.get("side", "")).startswith("stop")]
    stops = [o for o in r.get("orders") or [] if str(o.get("side", "")).startswith("stop")]
    research = r.get("research") or []

    if r.get("outcome") == "tick":
        what = STATUS.get(r.get("status"), r.get("status") or "—")
        tag = f"{SES.get(r.get('session'), r.get('session'))} · {len(orders)} {'orden' if len(orders) == 1 else 'órdenes'}"
    elif r.get("outcome"):
        what = OUTCOME.get(r["outcome"], r["outcome"])
        tag = what
    else:
        what = "el job falló antes de que el agente terminara" if job_status != "success" else "sin resultado del agente"
        tag = "error" if job_status != "success" else "sin resultado"
    if job_status not in ("success", ""):
        tag += " · job con error"

    subject = f"Agente trader · {ny:%H:%M} NY · {tag} · {usd(spent)}"
    lines = [
        f"Despertar del {DIAS[ny.weekday()]} {ny.day} {MESES[ny.month - 1]} {ny.year}" + (" (modo prueba: no envió órdenes)" if r.get("dry_run") else ""),
        "",
        f"Empezó:   {fmt_ny(start)}",
        f"Terminó:  {fmt_ny(end)}",
        f"Duró:     {secs // 60} min {secs % 60} s",
        f"Qué pasó: {what}" + (f" — {r['detail']}" if r.get("detail") else ""),
        "",
        "DINERO DE VERDAD",
        f"  LLM en este despertar: {usd(spent)}" + (f" (investigaciones: {usd(sum(x.get('usd') or 0 for x in research))})" if research else ""),
        f"  LLM en el mes:         {usd(month_spent(sd, month), 2)}" + (f" de {usd(cap, 2)}" if cap else ""),
        "  GitHub Actions:        $0 (los repos públicos no pagan minutos)",
        "  El gasto del LLM lo calcula el bot con los tokens y la tabla de precios de config.yaml;",
        "  la cifra oficial está en console.anthropic.com.",
    ]
    if r.get("outcome") == "tick":
        acct = r.get("account") or {}
        if acct.get("equity") is not None:
            pl = acct["equity"] - acct["last_equity"] if acct.get("last_equity") else None
            lines += ["", "CUENTA PAPER (dinero simulado)",
                      f"  Valor: {usd(acct['equity'], 0)}" + (f" · P&L de hoy {'+' if pl >= 0 else '-'}{usd(abs(pl), 0)}" if pl is not None else "")
                      + f" · {r.get('positions', 0)} posiciones"]
        if orders or stops or research:
            lines += ["", "LO QUE HIZO"]
            for o in orders:
                px = f"limitada a {o['limit_price']}" if o.get("limit_price") else "a mercado"
                lines.append(f"  {'Compra' if o['side'] == 'buy' else 'Venta'} {o['qty']} {o['symbol']} {px} → {o.get('status')}"
                             + (f" ({o['error']})" if o.get("error") else ""))
                if o.get("reason"):
                    lines.append(f"    Por qué: {o['reason']}")
            for o in stops:
                lines.append(f"  Stop de {o['symbol']} en {o.get('stop_price')} → {o.get('status')}")
            for x in research:
                lines.append(f"  Investigó {x['symbol']}: {x.get('rating') or x.get('status')} ({usd(x.get('usd') or 0, 3)})")
        if r.get("final"):
            lines += ["", "LO QUE DIJO EL AGENTE (texto generado por el modelo)", "  " + r["final"].replace("\n", "\n  ")]
        if r.get("error"):
            lines += ["", f"Error: {r['error']}"]
    if run_url or pages_url:
        lines += [""] + ([f"Detalle de esta corrida: {run_url}"] if run_url else []) + ([f"Dashboard: {pages_url}"] if pages_url else [])
    return subject, "\n".join(lines) + "\n"


def send(subject: str, body: str) -> str:
    user, pw = os.environ.get("GMAIL_USER", "").strip(), os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()
    if not user or not pw:
        return "sin GMAIL_USER o GMAIL_APP_PASSWORD: no se mandó correo"
    to = os.environ.get("EMAIL_TO", "").strip() or user
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, f"Agente trader <{user}>", to
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=30) as smtp:
        smtp.login(user, pw)
        smtp.send_message(msg)
    return "correo enviado"


def main(argv: list[str]) -> int:
    sd = state_dir()
    if argv[:1] == ["start"]:
        print(f"BOT_START={datetime.now(timezone.utc).isoformat(timespec='seconds')}")
        print(f"BOT_LEDGER_BEFORE={ledger_total(sd):.6f}")
        return 0
    start = datetime.fromisoformat(os.environ.get("BOT_START") or datetime.now(timezone.utc).isoformat())
    spent = max(ledger_total(sd) - float(os.environ.get("BOT_LEDGER_BEFORE") or 0), 0.0)
    result = None
    if os.environ.get("BOT_RESULT_PATH"):
        try:
            result = json.loads(Path(os.environ["BOT_RESULT_PATH"]).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            result = None
    subject, body = build(start, datetime.now(timezone.utc), spent, result, os.environ.get("JOB_STATUS", ""), sd,
                          os.environ.get("RUN_URL", ""), os.environ.get("PAGES_URL", ""))
    print(subject)
    try:
        print(send(subject, body))
    except (smtplib.SMTPException, OSError) as exc:
        print(f"no se pudo mandar el correo: {type(exc).__name__}: {exc}")    # el correo nunca tumba el despertar
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
