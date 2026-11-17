"""Ejecución en Alpaca PAPER.

``AlpacaPaperBroker`` solo sabe hablar con https://paper-api.alpaca.markets: el cliente
se crea con ``paper=True`` y se verifica el host antes de hacer nada. Unas llaves de
cuenta real no autentican contra ese host, así que este bot no puede tocar dinero real.

Reglas de Alpaca que el agente debe respetar (docs de Alpaca, nov 2026):
  * en pre y post-market solo se aceptan órdenes LIMITADAS con extended_hours
  * los stops no se activan fuera del horario regular

``FakeBroker`` imita lo mismo para la demo y los tests.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

PAPER_HOST = "paper-api.alpaca.markets"
NY = ZoneInfo("America/New_York")


def _val(x) -> str:
    return str(getattr(x, "value", x))


def _f(x):
    return float(x) if x not in (None, "") else None


class AlpacaPaperBroker:
    name = "Alpaca paper"

    def __init__(self) -> None:
        from alpaca.trading.client import TradingClient

        self.client = TradingClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"], paper=True)
        base = getattr(self.client, "_base_url", "")
        base = str(getattr(base, "value", base))
        if PAPER_HOST not in base:
            raise RuntimeError(f"el cliente de Alpaca no apunta a paper ({base!r}); el bot no continúa")

    # ── lectura ──
    def account(self) -> dict:
        a = self.client.get_account()
        return {"equity": float(a.equity), "cash": float(a.cash), "buying_power": float(a.buying_power),
                "last_equity": _f(a.last_equity)}

    def positions(self) -> dict[str, dict]:
        out = {}
        for p in self.client.get_all_positions():
            qty = abs(float(p.qty)) * (-1 if _val(p.side).lower() == "short" else 1)
            out[p.symbol] = {"qty": qty, "avg_price": float(p.avg_entry_price), "price": _f(p.current_price),
                             "market_value": _f(p.market_value), "unrealized_pl": _f(p.unrealized_pl)}
        return out

    def is_market_day(self, d: date) -> bool:
        from alpaca.trading.requests import GetCalendarRequest

        return any(c.date == d for c in self.client.get_calendar(GetCalendarRequest(start=d, end=d)))

    def asset(self, symbol: str) -> dict:
        a = self.client.get_asset(symbol)
        return {"tradable": bool(a.tradable), "shortable": bool(a.shortable), "easy_to_borrow": bool(a.easy_to_borrow)}

    def screener_candidates(self, top: int = 50) -> list[dict]:
        """Las que más suben, las que más bajan y las más activas de todo EE. UU. (screener de Alpaca)."""
        from alpaca.data.enums import MarketType, MostActivesBy
        from alpaca.data.historical.screener import ScreenerClient
        from alpaca.data.requests import MarketMoversRequest, MostActivesRequest

        sc = ScreenerClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"])
        out = []
        mv = sc.get_market_movers(MarketMoversRequest(top=min(top, 50), market_type=MarketType.STOCKS))
        for src, rows in (("sube", mv.gainers), ("baja", mv.losers)):
            out += [{"symbol": m.symbol, "source": src, "price": float(m.price), "pct": float(m.percent_change) / 100} for m in rows]
        act = sc.get_most_actives(MostActivesRequest(top=min(top, 100), by=MostActivesBy.VOLUME))
        out += [{"symbol": a.symbol, "source": "activa", "volume": float(a.volume)} for a in act.most_actives]
        return out

    def tradable_symbols(self) -> set[str]:
        from alpaca.trading.enums import AssetClass, AssetStatus
        from alpaca.trading.requests import GetAssetsRequest

        assets = self.client.get_all_assets(GetAssetsRequest(status=AssetStatus.ACTIVE, asset_class=AssetClass.US_EQUITY))
        return {a.symbol for a in assets if a.tradable}

    def open_orders(self) -> list[dict]:
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        return [{"id": str(o.id), "symbol": o.symbol, "side": _val(o.side), "type": _val(o.type), "qty": float(o.qty or 0),
                 "limit_price": _f(o.limit_price), "stop_price": _f(o.stop_price), "status": _val(o.status),
                 "extended_hours": bool(o.extended_hours),
                 "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None}
                for o in self.client.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN, limit=200))]

    # ── órdenes ──
    def place(self, symbol: str, qty: int, limit_price: float | None = None, extended: bool = False) -> dict:
        """``qty`` con signo (negativo = vender). Sin precio límite = a mercado (solo en
        horario regular). En pre/post-market debe llevar límite y ``extended=True``."""
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

        side = OrderSide.BUY if qty > 0 else OrderSide.SELL
        if limit_price is None:
            req = MarketOrderRequest(symbol=symbol, qty=abs(int(qty)), side=side, time_in_force=TimeInForce.DAY)
        else:
            req = LimitOrderRequest(symbol=symbol, qty=abs(int(qty)), side=side, time_in_force=TimeInForce.DAY,
                                    limit_price=round(float(limit_price), 2), extended_hours=bool(extended))
        o = self.client.submit_order(req)
        return {"id": str(o.id), "status": _val(o.status)}

    def place_stop(self, symbol: str, qty: int, stop_price: float) -> dict:
        """Stop GTC que cubre ``qty`` (con signo de la orden de salida). Solo se activa en
        horario regular."""
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import StopOrderRequest

        o = self.client.submit_order(StopOrderRequest(symbol=symbol, qty=abs(int(qty)),
                                                      side=OrderSide.BUY if qty > 0 else OrderSide.SELL,
                                                      time_in_force=TimeInForce.GTC, stop_price=round(float(stop_price), 2)))
        return {"id": str(o.id), "status": _val(o.status)}

    def cancel(self, order_id: str) -> None:
        self.client.cancel_order_by_id(order_id)

    # ── historial ──
    def _orders(self, **kw) -> list:
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        return self.client.get_orders(GetOrdersRequest(status=QueryOrderStatus.ALL, limit=500, nested=True, **kw))

    def recent_orders(self, limit: int = 100) -> list[dict]:
        rows = []
        for parent in self._orders():
            for o in [parent, *(parent.legs or [])]:
                rows.append({"id": str(o.id), "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None, "symbol": o.symbol,
                             "limit_price": _f(o.limit_price), "stop_price": _f(o.stop_price), "extended_hours": bool(o.extended_hours),
                             "side": _val(o.side), "type": _val(o.type), "qty": float(o.qty or 0),
                             "filled_qty": float(o.filled_qty or 0), "filled_avg_price": _f(o.filled_avg_price),
                             "status": _val(o.status)})
        return rows[:limit]

    def fills_since(self, d: date) -> list[dict]:
        start = datetime(d.year, d.month, d.day, tzinfo=NY)
        fills = []
        for parent in self._orders(after=start):
            for o in [parent, *(parent.legs or [])]:
                if o.filled_at and float(o.filled_qty or 0) > 0 and o.filled_at.astimezone(NY).date() >= d:
                    fills.append({"symbol": o.symbol, "side": _val(o.side), "qty": float(o.filled_qty),
                                  "price": float(o.filled_avg_price), "at": o.filled_at.isoformat(), "id": str(o.id)})
        return sorted(fills, key=lambda f: f["at"])

    def equity_history(self) -> list[dict]:
        from alpaca.trading.requests import GetPortfolioHistoryRequest

        h = self.client.get_portfolio_history(GetPortfolioHistoryRequest(period="1A", timeframe="1D"))
        return [{"date": datetime.fromtimestamp(ts, timezone.utc).date().isoformat(), "equity": float(eq)}
                for ts, eq in zip(h.timestamp, h.equity) if eq]


class FakeBroker:
    """Cuenta simulada: posiciones persistentes, órdenes a mercado y limitadas, stops que
    solo se activan en horario regular, 2× de buying power (Reg T)."""

    name = "Simulado (demo)"

    def __init__(self, path: Path, starting_cash: float = 100_000.0):
        self.path = Path(path)
        if self.path.exists():
            self.state = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self.state = {"cash": starting_cash, "positions": {}, "orders": [], "fills": [], "equity_history": [],
                          "prices": {}, "clock": None, "session": "regular", "last_equity": starting_cash, "next_id": 1,
                          "shortable": True}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.state, indent=1), encoding="utf-8")

    def _px(self, sym: str) -> float:
        return float(self.state["prices"].get(sym) or self.state["positions"].get(sym, {}).get("avg_price") or 0.0)

    def set_market(self, prices: dict[str, float], session: str, clock: str) -> None:
        """Mueve el reloj del simulador y ejecuta lo que corresponda a esos precios."""
        self.state["prices"].update({k: float(v) for k, v in prices.items() if v})
        self.state["session"], self.state["clock"] = session, clock
        for o in [o for o in self.state["orders"] if o["status"] == "accepted"]:
            px = self._px(o["symbol"])
            if not px:
                continue
            if o["type"] == "stop":
                if session == "regular" and ((o["qty"] < 0 and px <= o["stop_price"]) or (o["qty"] > 0 and px >= o["stop_price"])):
                    self._fill(o, px)
            elif o["type"] == "limit":
                if session in ("pre", "post") and not o["extended_hours"]:
                    continue
                if (o["qty"] > 0 and px <= o["limit_price"]) or (o["qty"] < 0 and px >= o["limit_price"]):
                    self._fill(o, px)
            elif session == "regular":
                self._fill(o, px)
        self.save()

    def _fill(self, o: dict, px: float) -> None:
        sym, q = o["symbol"], o["qty"]
        pos = self.state["positions"].get(sym, {"qty": 0, "avg_price": px})
        new = pos["qty"] + q
        if pos["qty"] == 0 or (pos["qty"] > 0) == (q > 0):
            pos["avg_price"] = (abs(pos["qty"]) * pos["avg_price"] + abs(q) * px) / (abs(pos["qty"]) + abs(q))
        elif (pos["qty"] > 0) != (new > 0) and new != 0:
            pos["avg_price"] = px
        self.state["cash"] -= q * px
        if abs(new) < 1e-9:
            self.state["positions"].pop(sym, None)
        else:
            pos["qty"] = new
            self.state["positions"][sym] = pos
        o["status"], o["filled_avg_price"] = "filled", round(px, 4)
        self.state["fills"].append({"symbol": sym, "side": "buy" if q > 0 else "sell", "qty": abs(q), "price": round(px, 4),
                                    "at": self.state["clock"], "id": o["id"]})

    def account(self) -> dict:
        gross = sum(abs(p["qty"]) * self._px(s) for s, p in self.state["positions"].items())
        equity = self.state["cash"] + sum(p["qty"] * self._px(s) for s, p in self.state["positions"].items())
        return {"equity": equity, "cash": self.state["cash"], "buying_power": max(2 * equity - gross, 0.0),
                "last_equity": self.state["last_equity"]}

    def positions(self) -> dict[str, dict]:
        return {s: {"qty": p["qty"], "avg_price": p["avg_price"], "price": self._px(s), "market_value": p["qty"] * self._px(s),
                    "unrealized_pl": p["qty"] * (self._px(s) - p["avg_price"])} for s, p in self.state["positions"].items()}

    def is_market_day(self, d: date) -> bool:
        return d.weekday() < 5

    def asset(self, symbol: str) -> dict:
        return {"tradable": True, "shortable": bool(self.state.get("shortable", True)), "easy_to_borrow": True}

    def open_orders(self) -> list[dict]:
        return [{k: o.get(k) for k in ("id", "symbol", "side", "type", "qty", "limit_price", "stop_price", "status",
                                         "extended_hours", "submitted_at")} for o in self.state["orders"] if o["status"] == "accepted"]

    def _submit(self, symbol, qty, typ, limit_price=None, stop_price=None, extended=False) -> dict:
        session = self.state["session"]
        if typ == "market" and session != "regular":
            raise RuntimeError("market orders are not accepted outside regular trading hours")
        if typ == "stop" and extended:
            raise RuntimeError("stop orders are not eligible for extended hours trading")
        if typ == "limit" and session in ("pre", "post") and not extended:
            raise RuntimeError("limit order not eligible for extended hours")
        acct, px = self.account(), self._px(symbol)
        cur = self.state["positions"].get(symbol, {}).get("qty", 0)
        opening = abs(cur + qty) > abs(cur)
        if typ != "stop" and opening and abs(qty) * px > acct["buying_power"]:
            raise RuntimeError("insufficient buying power")
        if typ != "stop" and qty < 0 < cur:
            reserved = sum(-o["qty"] for o in self.state["orders"] if o["status"] == "accepted" and o["symbol"] == symbol and o["qty"] < 0)
            if reserved + abs(qty) > cur and reserved:
                raise RuntimeError(f"insufficient qty available for order (requested: {abs(qty)}, available: {max(cur - reserved, 0)})")
        oid = f"sim-{self.state['next_id']}"
        self.state["next_id"] += 1
        o = {"id": oid, "symbol": symbol, "side": "buy" if qty > 0 else "sell", "type": typ, "qty": int(qty),
             "limit_price": limit_price, "stop_price": stop_price, "status": "accepted", "extended_hours": bool(extended),
             "submitted_at": self.state["clock"]}
        self.state["orders"].append(o)
        self.set_market({}, session, self.state["clock"])   # ejecuta si ya es ejecutable
        return {"id": oid, "status": o["status"]}

    def place(self, symbol: str, qty: int, limit_price: float | None = None, extended: bool = False) -> dict:
        return self._submit(symbol, qty, "market" if limit_price is None else "limit", limit_price=limit_price, extended=extended)

    def place_stop(self, symbol: str, qty: int, stop_price: float) -> dict:
        return self._submit(symbol, qty, "stop", stop_price=stop_price)

    def cancel(self, order_id: str) -> None:
        for o in self.state["orders"]:
            if o["id"] == order_id and o["status"] == "accepted":
                o["status"] = "canceled"
                self.save()
                return
        raise RuntimeError(f"order {order_id} not found or not open")

    def close_day(self, d: date) -> None:
        """Al terminar la sesión simulada: expiran las órdenes del día y se anota el equity."""
        for o in self.state["orders"]:
            if o["status"] == "accepted" and o["type"] != "stop":
                o["status"] = "expired"
        eq = round(self.account()["equity"], 2)
        self.state["equity_history"] = [x for x in self.state["equity_history"] if x["date"] != d.isoformat()] + [{"date": d.isoformat(), "equity": eq}]
        self.state["last_equity"] = eq
        self.save()

    def fills_since(self, d: date) -> list[dict]:
        return [f for f in self.state["fills"] if (f["at"] or "")[:10] >= d.isoformat()]

    def recent_orders(self, limit: int = 100) -> list[dict]:
        return [{"id": o["id"], "submitted_at": o["submitted_at"], "symbol": o["symbol"], "side": o["side"], "type": o["type"], "qty": abs(o["qty"]),
                 "limit_price": o.get("limit_price"), "stop_price": o.get("stop_price"), "extended_hours": o.get("extended_hours", False),
                 "filled_qty": abs(o["qty"]) if o["status"] == "filled" else 0, "filled_avg_price": o.get("filled_avg_price"),
                 "status": o["status"]} for o in reversed(self.state["orders"])][:limit]

    def equity_history(self) -> list[dict]:
        return self.state["equity_history"]
