"""
core/ws_manager.py
Manages all active WebSocket connections.
broadcast() sends a JSON payload to every connected client.
"""

import json
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.append(ws)
        print(f"📡 WS client connected — total: {len(self._connections)}")

    def disconnect(self, ws: WebSocket):
        if ws in self._connections:
            self._connections.remove(ws)
        print(f"📡 WS client disconnected — total: {len(self._connections)}")

    async def broadcast(self, payload: dict):
        message = json.dumps(payload)
        dead = []
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_to(self, ws: WebSocket, payload: dict):
        await ws.send_text(json.dumps(payload))

    @property
    def connection_count(self):
        return len(self._connections)


# Module-level singleton imported by scheduler and websocket router
manager = ConnectionManager()
