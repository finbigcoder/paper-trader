"""El correo de cada despertar, sin red."""
import json
from datetime import datetime, timedelta, timezone

from bot import notify
from bot.state import save_json

START = datetime(2026, 11, 16, 15, 8, 5, tzinfo=timezone.utc)            # 10:08 NY
TICK = {"outcome": "tick", "time": "10:08", "session": "regular", "status": "ok", "final": "Compré MU por momentum; vigilo 650.",
        "orders": [{"side": "buy", "qty": 10, "symbol": "MU", "limit_price": None, "status": "filled", "reason": "momentum #1"},
                   {"side": "stop (sell)", "qty": 10, "symbol": "MU", "stop_price": 640.0, "status": "accepted"}],
        "research": [{"symbol": "MU", "rating": "Buy", "usd": 0.041}],
        "account": {"equity": 101_250.0, "last_equity": 100_000.0}, "positions": 3, "cost": {"usd": 0.046}}


def ledger(sd, *usd):
    save_json(sd / "ledger.json", {"entries": [{"date": "2026-11-16", "usd": u} for u in usd]})


def test_email_has_start_end_duration_cost_and_what_it_did(tmp_path):
    ledger(tmp_path, 0.30, 0.046)
    subject, body = notify.build(START, START + timedelta(minutes=2, seconds=31), 0.046, TICK, "success", tmp_path,
                                 "https://github.com/x/y/actions/runs/1", "https://x.github.io/y/")
    assert subject == "Agente trader · 10:08 NY · horario regular · 1 orden · $0.0460"
    for needle in ("Empezó:   10:08:05 hora de Nueva York (15:08 UTC)", "Terminó:  10:10:36", "Duró:     2 min 31 s",
                   "LLM en este despertar: $0.0460 (investigaciones: $0.0410)", "LLM en el mes:         $0.35 de $20.00",
                   "GitHub Actions:        $0", "Compra 10 MU a mercado → filled", "Por qué: momentum #1", "Stop de MU en 640.0",
                   "Investigó MU: Buy", "P&L de hoy +$1,250", "Compré MU por momentum", "actions/runs/1", "x.github.io/y"):
        assert needle in body, needle


def test_email_when_it_did_not_trade_or_the_job_failed(tmp_path):
    s, b = notify.build(START, START, 0.0, {"outcome": "market_holiday", "detail": "el mercado no abre hoy"}, "success", tmp_path)
    assert "No operó: el mercado no abre hoy" in s and "$0.0000" in s
    s, b = notify.build(START, START, 0.012, None, "failure", tmp_path)
    assert "error · job con error" in s and "el job falló" in b and "$0.0120" in b


def test_cost_is_what_the_ledger_grew_during_the_run(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("BOT_STATE_DIR", str(tmp_path))
    ledger(tmp_path, 1.0)
    notify.main(["start"])
    env = dict(line.split("=", 1) for line in capsys.readouterr().out.split())
    assert env["BOT_LEDGER_BEFORE"] == "1.000000"
    ledger(tmp_path, 1.0, 0.004, 0.05)
    result = tmp_path / "r.json"
    result.write_text(json.dumps(TICK))
    for k, v in {**env, "BOT_RESULT_PATH": str(result), "JOB_STATUS": "success"}.items():
        monkeypatch.setenv(k, v)
    monkeypatch.delenv("GMAIL_USER", raising=False)
    assert notify.main(["send"]) == 0
    out = capsys.readouterr().out
    assert "$0.0540" in out and "no se mandó correo" in out


def test_sends_through_gmail_ssl_with_the_app_password(monkeypatch):
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, context=None, timeout=None):
            sent["server"] = (host, port)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def login(self, user, pw):
            sent["login"] = (user, pw)

        def send_message(self, msg):
            sent["msg"] = msg

    monkeypatch.setattr(notify.smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setenv("GMAIL_USER", "yo@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "abcd efgh ijkl mnop")
    monkeypatch.delenv("EMAIL_TO", raising=False)
    assert notify.send("Asunto", "Cuerpo") == "correo enviado"
    assert sent["server"] == ("smtp.gmail.com", 465) and sent["login"] == ("yo@example.com", "abcdefghijklmnop")
    assert sent["msg"]["To"] == "yo@example.com" and sent["msg"]["Subject"] == "Asunto"


def test_a_failed_email_never_breaks_the_run(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise notify.smtplib.SMTPAuthenticationError(535, b"bad")

    monkeypatch.setattr(notify.smtplib, "SMTP_SSL", boom)
    monkeypatch.setenv("BOT_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("GMAIL_USER", "yo@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "x")
    assert notify.main(["send"]) == 0


def test_tick_reports_missing_keys_for_the_email(tmp_path, monkeypatch):
    from bot import tick

    for k in tick.REQUIRED_ENV:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("BOT_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("BOT_RESULT_PATH", str(tmp_path / "r.json"))
    assert tick.main([]) == 0
    assert json.loads((tmp_path / "r.json").read_text())["outcome"] == "setup_incomplete"


def test_a_second_tick_within_ten_minutes_is_skipped_and_sends_no_email(tmp_path, monkeypatch, capsys):
    from bot import tick
    from bot.session import now_et

    sd = tmp_path / "state"
    for k in tick.REQUIRED_ENV:
        monkeypatch.setenv(k, "x")
    monkeypatch.setenv("BOT_STATE_DIR", str(sd))
    monkeypatch.setenv("BOT_RESULT_PATH", str(tmp_path / "r.json"))
    now = now_et()
    save_json(sd / "days" / f"{now.date()}.json", {"date": str(now.date()), "ticks": [{"at": now.isoformat(timespec="seconds")}]})
    assert tick.main([]) == 0                                   # sale antes de tocar Alpaca
    assert json.loads((tmp_path / "r.json").read_text())["outcome"] == "duplicate"
    monkeypatch.setenv("GMAIL_USER", "yo@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "x")
    monkeypatch.setattr(notify.smtplib, "SMTP_SSL", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no debía mandar")))
    assert notify.main(["send"]) == 0 and "no se manda correo" in capsys.readouterr().out
