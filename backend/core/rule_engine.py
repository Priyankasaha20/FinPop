"""
core/rule_engine.py
- Evaluates all active rules against live Kite quotes
- Fires Expo push notifications + saves alert history on trigger
- Parses plain-English rules via Claude API
"""

import httpx
import json
import asyncio
from datetime import datetime
import pytz

from core.database import (
    get_all_rules, mark_triggered, save_alert, get_push_tokens
)
from core.kite import fetch_quote, fetch_ohlc, is_market_open

IST = pytz.timezone("Asia/Kolkata")

# Cache opening prices per instrument, reset daily
_open_price_cache: dict[str, float] = {}
_cache_date: str = ""

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL   = "claude-sonnet-4-20250514"

NL_SYSTEM_PROMPT = """
Convert a plain English stock alert into a strict JSON object.
Output ONLY valid JSON — no markdown, no explanation.

Fields:
- instrument: string — "EXCHANGE:SYMBOL" format. Common mappings:
    Nifty / Nifty50 / NIFTY → "NSE:NIFTY 50"
    Sensex                  → "BSE:SENSEX"
    BankNifty               → "NSE:NIFTY BANK"
    Otherwise prefix "NSE:" to the symbol (e.g. "NSE:RELIANCE")
- condition: one of "above" | "below" | "pct_change_up" | "pct_change_down"
- threshold: float — percentage for pct_change variants, price for above/below
- timeframe: one of "from_open" | "from_prev_close" | "absolute"
- description: concise human-readable string

Example input:  "Alert if Nifty drops 1.5% from today's open"
Example output: {"instrument":"NSE:NIFTY 50","condition":"pct_change_down","threshold":1.5,"timeframe":"from_open","description":"Nifty drops 1.5% from open"}
""".strip()


# ── NL Parsing ─────────────────────────────────────────────────────────────────

async def parse_nl_rule(text: str, anthropic_api_key: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            CLAUDE_API_URL,
            headers={
                "x-api-key":         anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            },
            json={
                "model":    CLAUDE_MODEL,
                "max_tokens": 512,
                "system":   NL_SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": text}],
            },
            timeout=30.0,
        )
    resp.raise_for_status()
    raw = resp.json()["content"][0]["text"].strip()
    # Strip accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ── Evaluation Loop ────────────────────────────────────────────────────────────

async def evaluate_all_rules():
    """Called every 60s by the scheduler. Skips if market is closed."""
    if not is_market_open():
        return

    rules = get_all_rules(status="active")
    if not rules:
        return

    instruments = list({r["instrument"] for r in rules})

    try:
        quotes = fetch_quote(instruments)
    except Exception as e:
        print(f"❌ Quote fetch failed: {e}")
        return

    _refresh_open_cache(quotes)

    for rule in rules:
        try:
            _evaluate_rule(rule, quotes)
        except Exception as e:
            print(f"⚠️  Rule {rule['rule_id']} eval error: {e}")


def _refresh_open_cache(quotes: dict):
    global _cache_date
    today = datetime.now(IST).strftime("%Y-%m-%d")
    if _cache_date != today:
        _open_price_cache.clear()
        _cache_date = today

    for instrument, data in quotes.items():
        if instrument not in _open_price_cache:
            ohlc = data.get("ohlc", {})
            if ohlc.get("open"):
                _open_price_cache[instrument] = ohlc["open"]


def _evaluate_rule(rule: dict, quotes: dict):
    instrument = rule["instrument"]
    condition  = rule["condition"]
    threshold  = float(rule["threshold"])
    timeframe  = rule["timeframe"]

    q = quotes.get(instrument, {})
    last_price = q.get("last_price") or q.get("last_price", 0)
    if not last_price:
        return

    ref = _get_ref_price(instrument, timeframe, q)
    triggered = False

    if condition == "above":
        triggered = last_price > threshold

    elif condition == "below":
        triggered = last_price < threshold

    elif condition == "pct_change_down" and ref:
        drop_pct = ((ref - last_price) / ref) * 100
        triggered = drop_pct >= threshold

    elif condition == "pct_change_up" and ref:
        rise_pct = ((last_price - ref) / ref) * 100
        triggered = rise_pct >= threshold

    if triggered:
        asyncio.create_task(_fire_alert(rule, last_price))


def _get_ref_price(instrument: str, timeframe: str, quote: dict) -> float | None:
    if timeframe == "from_open":
        return _open_price_cache.get(instrument) or quote.get("ohlc", {}).get("open")
    elif timeframe == "from_prev_close":
        return quote.get("ohlc", {}).get("close")
    return None  # absolute — no ref needed


# ── Alert Firing ───────────────────────────────────────────────────────────────

async def _fire_alert(rule: dict, price: float):
    rule_id     = rule["rule_id"]
    instrument  = rule["instrument"]
    description = rule["description"]

    print(f"🚨 ALERT TRIGGERED: {description} | {instrument} @ ₹{price:,.2f}")

    mark_triggered(rule_id)
    save_alert({
        "rule_id":       rule_id,
        "instrument":    instrument,
        "trigger_price": price,
        "description":   description,
    })

    await send_push_to_all(
        title=f"🚨 {instrument}",
        body=f"{description}\nPrice: ₹{price:,.2f}",
        data={"rule_id": rule_id, "instrument": instrument, "price": price},
    )


# ── Expo Push ──────────────────────────────────────────────────────────────────

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

async def send_push_to_all(title: str, body: str, data: dict = None):
    tokens = get_push_tokens()
    if not tokens:
        print("⚠️  No push tokens — alert not delivered to phone")
        return

    messages = [
        {
            "to":       token,
            "title":    title,
            "body":     body,
            "data":     data or {},
            "sound":    "default",
            "priority": "high",
            "channelId": "trade-alerts",
        }
        for token in tokens
    ]

    async with httpx.AsyncClient() as client:
        for i in range(0, len(messages), 100):
            batch = messages[i:i+100]
            try:
                resp = await client.post(
                    EXPO_PUSH_URL,
                    json=batch,
                    headers={"Content-Type": "application/json"},
                    timeout=15.0,
                )
                for item in resp.json().get("data", []):
                    if item.get("status") == "error":
                        print(f"⚠️  Push error: {item.get('message')}")
                    else:
                        print(f"📲 Push delivered: {item.get('id')}")
            except Exception as e:
                print(f"❌ Push failed: {e}")
