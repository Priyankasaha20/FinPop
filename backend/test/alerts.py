"""
routers/alerts.py
Alert history endpoints.
"""

from fastapi import APIRouter
from core.database import get_alert_history

router = APIRouter()


@router.get("/history")
async def alert_history(limit: int = 100):
    """Returns the last N triggered alerts in reverse chronological order."""
    return get_alert_history(limit=limit)
