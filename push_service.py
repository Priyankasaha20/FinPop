"""
push_service.py
Sends push notifications to the mobile app via Expo's push API.
Add these routes to main.py and call send_push_notification() from rule_engine.py.
"""

import httpx
import sqlite3
from pathlib import Path

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
DB_PATH = Path(__file__).parent / "alerts.db"


# ── Token Storage ──────────────────────────────────────────────────────────────

def init_push_table():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS push_tokens (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                token      TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def save_push_token(token: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO push_tokens (token) VALUES (?)", (token,)
        )
        conn.commit()


def get_push_tokens() -> list[str]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT token FROM push_tokens").fetchall()
    return [r[0] for r in rows]


# ── Sending ────────────────────────────────────────────────────────────────────

async def send_push_notification(title: str, body: str, data: dict = None):
    """
    Send a push notification to all registered Expo tokens.
    Called from notifier.py alongside Telegram/email.
    """
    tokens = get_push_tokens()
    if not tokens:
        print("⚠️  No push tokens registered — skipping push notification")
        return

    messages = [
        {
            "to":    token,
            "title": title,
            "body":  body,
            "data":  data or {},
            "sound": "default",
            "priority": "high",
            # Android
            "channelId": "trade-alerts",
        }
        for token in tokens
    ]

    # Expo accepts up to 100 messages per request
    async with httpx.AsyncClient() as client:
        for i in range(0, len(messages), 100):
            batch = messages[i : i + 100]
            resp = await client.post(
                EXPO_PUSH_URL,
                json=batch,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                timeout=15.0,
            )
            result = resp.json()
            for item in result.get("data", []):
                if item.get("status") == "error":
                    print(f"⚠️  Push error: {item.get('message')} — {item.get('details')}")
                else:
                    print(f"📲 Push sent: {item.get('id')}")


# ── FastAPI Routes (paste these into main.py) ──────────────────────────────────
"""
Add these two routes to your main.py:

from push_service import init_push_table, save_push_token, send_push_notification
from pydantic import BaseModel

class PushTokenRequest(BaseModel):
    token: str

@app.on_event("startup")
async def startup():
    init_db()
    init_push_table()   # <-- add this line

@app.post("/api/push/register")
async def register_push_token(req: PushTokenRequest):
    save_push_token(req.token)
    return {"status": "registered"}
"""
