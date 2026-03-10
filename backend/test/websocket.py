"""
routers/websocket.py
WebSocket endpoint.
Mobile app connects once and receives live portfolio updates every 30s.
Also receives real-time alert events the moment a rule fires.

Connect from React Native:
    const ws = new WebSocket('ws://10.57.170.125:8000/ws/portfolio');
    ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'portfolio_update') { ... }
        if (data.type === 'alert_triggered')  { ... }
    };
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.ws_manager import manager
from core.kite import fetch_holdings, fetch_margins

router = APIRouter()


@router.websocket("/portfolio")
async def portfolio_ws(ws: WebSocket):
    await manager.connect(ws)

    # Send an immediate snapshot on connect so the app doesn't wait 30s
    try:
        snapshot = {
            "type":     "portfolio_update",
            "holdings": fetch_holdings(),
            "margins":  fetch_margins(),
        }
        await manager.send_to(ws, snapshot)
    except Exception as e:
        print(f"⚠️  Initial snapshot error: {e}")

    try:
        # Keep connection alive — client can send pings if needed
        while True:
            text = await ws.receive_text()
            if text == "ping":
                await manager.send_to(ws, {"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception as e:
        print(f"WS error: {e}")
        manager.disconnect(ws)
