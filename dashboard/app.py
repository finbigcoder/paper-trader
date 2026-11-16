#!/usr/bin/env python3
"""Dashboard local del bot. No instala nada: solo necesita Python 3.9+ y git.

    python3 dashboard/app.py                  lee state/ (lo que el bot sube al repo)
    python3 dashboard/app.py --demo           lee state_demo/ (datos de ejemplo)
    python3 dashboard/app.py --export site    escribe la versión web estática en site/
                                              (la que GitHub Actions publica en GitHub Pages)

Abre http://127.0.0.1:8765 en tu navegador. Solo escucha en tu propia máquina.
El dashboard es de solo lectura: no guarda llaves y no puede mandar órdenes.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import threading
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
STATE = ROOT / "state"
DEMO = False
REPORT_RE = re.compile(r"^reports/\d{4}-\d{2}-\d{2}/[A-Z][A-Z0-9.]{0,7}\.md$")


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def git(*args: str) -> tuple[int, str]:
    try:
        out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=60)
        return out.returncode, (out.stdout + out.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, f"{type(exc).__name__}: {exc}"


def repo_info() -> dict:
    code, url = git("config", "--get", "remote.origin.url")
    if code != 0 or not url:
        return {}
    m = re.search(r"github\.com[:/]([\w.-]+)/([\w.-]+?)(?:\.git)?$", url)
    if not m:
        return {}
    base = f"https://github.com/{m.group(1)}/{m.group(2)}"
    return {"url": base, "actions_url": f"{base}/actions/workflows/bot.yml",
            "secrets_url": f"{base}/settings/secrets/actions"}


def config_value(key: str) -> str | None:
    try:
        text = (ROOT / "config.yaml").read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(rf"^\s*{key}:\s*([^\s#]+)", text, re.M)
    return m.group(1).strip("\"'") if m else None


def config_cap() -> float | None:
    v = config_value("monthly_usd")
    try:
        return float(v) if v else None
    except ValueError:
        return None


def slim_day(d: dict) -> dict:
    """El día sin la tabla de estadísticas de todo el universo (pesa mucho y el tablero no la usa)."""
    prep = dict(d.get("prep") or {})
    prep.pop("stats", None)
    prep["ranking"] = (prep.get("ranking") or [])[:15]
    return {**d, "prep": prep}


def build_state() -> dict:
    days = []
    for p in sorted((STATE / "days").glob("*.json")):
        d = read_json(p)
        if d and d.get("ticks"):
            days.append(slim_day(d))
    lessons = STATE / "agent" / "lessons.md"
    return {
        "demo": DEMO,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": read_json(STATE / "status.json", {}),
        "snapshot": read_json(STATE / "snapshot.json"),
        "benchmark": read_json(STATE / "benchmark.json"),
        "ledger": read_json(STATE / "ledger.json", {"entries": []}),
        "journal": read_json(STATE / "journal.json", []),
        "fills": read_json(STATE / "fills.json", []),
        "virtual": read_json(STATE / "virtual.json", []),
        "research": read_json(STATE / "research.json", []),
        "lessons": lessons.read_text(encoding="utf-8") if lessons.exists() else None,
        "days": days,
        "cap": config_cap(),
        "model": config_value("trader_model"),
        "tick_minutes": config_value("tick_minutes"),
        "repo": repo_info(),
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:  # silencio en la terminal
        pass

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200) -> None:
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        path, _, query = self.path.partition("?")
        if path in ("/", "/index.html"):
            self._send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif path == "/favicon.ico":
            self._send(204, b"", "image/x-icon")
        elif path == "/api/state":
            self._json(build_state())
        elif path == "/api/report":
            rel = dict(p.split("=", 1) for p in query.split("&") if "=" in p).get("path", "").replace("%2F", "/")
            target = STATE / rel
            if not REPORT_RE.match(rel) or not target.is_file():
                self._json({"error": "reporte no encontrado"}, 404)
            else:
                self._send(200, target.read_bytes(), "text/plain; charset=utf-8")
        else:
            self._json({"error": "no existe"}, 404)

    def do_POST(self) -> None:
        if self.path != "/api/sync":
            self._json({"error": "no existe"}, 404)
            return
        # Solo se acepta desde la propia página (evita que otro sitio dispare el pull).
        if self.headers.get("X-Dashboard") != "1":
            self._json({"error": "solicitud no permitida"}, 403)
            return
        code, out = git("pull", "--ff-only")
        self._json({"ok": code == 0, "output": out[-600:]})


def export(out: Path) -> dict:
    """Versión estática para GitHub Pages: la misma página, el estado en un JSON y los
    reportes de TradingAgents. Sin servidor: la página se recarga sola cada minuto."""
    import shutil

    out.mkdir(parents=True, exist_ok=True)
    state = build_state()
    state["static"] = True
    reports = []
    for d in state["days"]:
        for t in d["ticks"]:
            reports += [r.get("report") for r in t.get("research", []) if r.get("report")]
    for rel in sorted(set(reports)):
        src = STATE / rel
        if REPORT_RE.match(rel) and src.is_file():
            (out / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, out / rel)
    (out / "state.json").write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    html = (HERE / "index.html").read_text(encoding="utf-8").replace(
        "<head>", '<head>\n<meta name="robots" content="noindex, nofollow">\n<script>window.STATIC_SITE = true;</script>', 1)
    (out / "index.html").write_text(html, encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    return {"days": len(state["days"]), "reports": len(set(reports))}


def main() -> None:
    global STATE, DEMO
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demo", action="store_true", help="usar los datos de ejemplo de state_demo/")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--export", metavar="CARPETA", help="escribir la versión web estática y salir")
    args = ap.parse_args()
    if args.demo:
        STATE, DEMO = ROOT / "state_demo", True
    if args.export:
        info = export(Path(args.export))
        print(f"versión web escrita en {args.export}: {info['days']} días, {info['reports']} reportes")
        return
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}"
    print(f"Dashboard en {url}  ({'demo' if DEMO else 'datos reales'}: {STATE})\nCtrl+C para cerrar.")
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\ncerrado.")


if __name__ == "__main__":
    main()
