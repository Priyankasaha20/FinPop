"""
core/scheduler.py
APScheduler-based background jobs:
  - Every 60s  : evaluate all active rules against live quotes
  - Every 30s  : refresh portfolio snapshot, broadcast via WebSocket
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio

from core.rule_engine import evaluate_all_rules
from core.kite import fetch_holdings, fetch_margins, is_market_open
from core import ws_manager  # WebSocket connection manager

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


async def _rule_check_job():
    try:
        await evaluate_all_rules()
    except Exception as e:
        print(f"❌ Rule check error: {e}")


async def _portfolio_broadcast_job():
    """Fetch latest portfolio data and push to all connected WebSocket clients."""
    if not is_market_open():
        return
    try:
        holdings = fetch_holdings()
        margins  = fetch_margins()
        payload  = {
            "type":     "portfolio_update",
            "holdings": holdings,
            "margins":  margins,
        }
        await ws_manager.broadcast(payload)
    except Exception as e:
        print(f"❌ Portfolio broadcast error: {e}")


async def start_scheduler():
    scheduler.add_job(
        _rule_check_job,
        trigger=IntervalTrigger(seconds=60),
        id="rule_check",
        replace_existing=True,
    )
    scheduler.add_job(
        _portfolio_broadcast_job,
        trigger=IntervalTrigger(seconds=30),
        id="portfolio_broadcast",
        replace_existing=True,
    )
    scheduler.start()


async def stop_scheduler():
    scheduler.shutdown(wait=False)
