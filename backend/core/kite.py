"""
core/kite.py
Kite Connect wrapper.
Holds a single KiteConnect instance refreshed after each login.
"""

from kiteconnect import KiteConnect
from datetime import datetime, time
import pytz
import os

from core.database import get_session, save_session

IST = pytz.timezone("Asia/Kolkata")
MARKET_OPEN  = time(9, 15)
MARKET_CLOSE = time(15, 30)

# Module-level singleton
_kite: KiteConnect | None = None


def get_kite() -> KiteConnect | None:
    return _kite


def init_kite_from_db() -> bool:
    """Called at startup — restores session from DB if it exists."""
    global _kite
    session = get_session()
    if not session or not session.get("access_token"):
        return False
    _kite = KiteConnect(api_key=session["api_key"])
    _kite.set_access_token(session["access_token"])
    print(f"✅ Kite session restored for {session.get('user_name')}")
    return True


def create_kite_session(api_key: str, api_secret: str, request_token: str) -> dict:
    """
    Exchange request_token for access_token after OAuth.
    Returns user profile dict.
    """
    global _kite
    kite = KiteConnect(api_key=api_key)
    data = kite.generate_session(request_token, api_secret=api_secret)

    _kite = kite
    _kite.set_access_token(data["access_token"])

    save_session(
        api_key=api_key,
        access_token=data["access_token"],
        user_id=data.get("user_id", ""),
        user_name=data.get("user_name", ""),
    )
    return data


def get_login_url(api_key: str) -> str:
    kite = KiteConnect(api_key=api_key)
    return kite.login_url()


# ── Portfolio Fetchers ─────────────────────────────────────────────────────────

def fetch_holdings() -> list[dict]:
    if not _kite:
        return _mock_holdings()
    raw = _kite.holdings()
    return [
        {
            "tradingsymbol": h["tradingsymbol"],
            "exchange":      h["exchange"],
            "quantity":      h["quantity"],
            "average_price": h["average_price"],
            "last_price":    h["last_price"],
            "pnl":           h["pnl"],
            "pnl_pct":       round((h["pnl"] / (h["average_price"] * h["quantity"])) * 100, 2)
                             if h["average_price"] and h["quantity"] else 0,
            "current_value": round(h["last_price"] * h["quantity"], 2),
            "invested_value":round(h["average_price"] * h["quantity"], 2),
        }
        for h in raw
    ]


def fetch_orders() -> list[dict]:
    if not _kite:
        return _mock_orders()
    raw = _kite.orders()
    return [
        {
            "order_id":       o["order_id"],
            "tradingsymbol":  o["tradingsymbol"],
            "exchange":       o["exchange"],
            "transaction_type": o["transaction_type"],
            "quantity":       o["quantity"],
            "price":          o["price"],
            "average_price":  o["average_price"],
            "status":         o["status"],
            "order_type":     o["order_type"],
            "placed_at":      str(o.get("order_timestamp", "")),
        }
        for o in raw
    ]


def fetch_margins() -> dict:
    if not _kite:
        return _mock_margins()
    raw = _kite.margins()
    equity = raw.get("equity", {})
    commodity = raw.get("commodity", {})
    return {
        "equity": {
            "available_cash":    equity.get("available", {}).get("cash", 0),
            "used_margin":       equity.get("utilised", {}).get("debits", 0),
            "total_balance":     equity.get("net", 0),
            "opening_balance":   equity.get("available", {}).get("opening_balance", 0),
        },
        "commodity": {
            "available_cash":    commodity.get("available", {}).get("cash", 0),
            "used_margin":       commodity.get("utilised", {}).get("debits", 0),
            "total_balance":     commodity.get("net", 0),
        },
    }


def fetch_quote(instruments: list[str]) -> dict:
    """instruments: ["NSE:NIFTY 50", "NSE:RELIANCE", ...]"""
    if not _kite:
        return {i: {"last_price": 0, "mock": True} for i in instruments}
    return _kite.quote(instruments)


def fetch_ohlc(instruments: list[str]) -> dict:
    if not _kite:
        return {}
    return _kite.ohlc(instruments)


# ── Market Hours ───────────────────────────────────────────────────────────────

def is_market_open() -> bool:
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    return MARKET_OPEN <= now.time() <= MARKET_CLOSE


# ── Mock Data (dev without Kite) ───────────────────────────────────────────────

def _mock_holdings():
    import random
    stocks = [
        ("RELIANCE", "NSE", 10, 2800, 2952),
        ("TCS",      "NSE",  5, 3600, 3847),
        ("INFY",     "NSE", 20, 1400, 1520),
        ("HDFCBANK", "NSE", 15, 1550, 1620),
    ]
    holdings = []
    for sym, ex, qty, avg, ltp in stocks:
        ltp += random.uniform(-20, 20)
        pnl = (ltp - avg) * qty
        holdings.append({
            "tradingsymbol": sym, "exchange": ex,
            "quantity": qty, "average_price": avg,
            "last_price": round(ltp, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": round((pnl / (avg * qty)) * 100, 2),
            "current_value": round(ltp * qty, 2),
            "invested_value": avg * qty,
        })
    return holdings


def _mock_orders():
    return [
        {
            "order_id": "240101000001",
            "tradingsymbol": "RELIANCE", "exchange": "NSE",
            "transaction_type": "BUY", "quantity": 5,
            "price": 2900.0, "average_price": 2898.5,
            "status": "COMPLETE", "order_type": "LIMIT",
            "placed_at": "2026-03-09 10:15:00",
        },
        {
            "order_id": "240101000002",
            "tradingsymbol": "TCS", "exchange": "NSE",
            "transaction_type": "SELL", "quantity": 2,
            "price": 3850.0, "average_price": 3848.0,
            "status": "COMPLETE", "order_type": "LIMIT",
            "placed_at": "2026-03-09 11:42:00",
        },
    ]


def _mock_margins():
    return {
        "equity": {
            "available_cash": 52340.75,
            "used_margin":    18200.00,
            "total_balance":  70540.75,
            "opening_balance":72000.00,
        },
        "commodity": {
            "available_cash": 10000.00,
            "used_margin":    0,
            "total_balance":  10000.00,
        },
    }
