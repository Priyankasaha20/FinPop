"""
finpop-backend — main.py
FastAPI server with:
  - Kite Connect OAuth + session management
  - Portfolio data (holdings, orders, margins)
  - WebSocket for live data push to mobile app
  - Rule engine (plain English via Claude + preset conditions)
  - Expo push notifications on rule trigger

Run:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from core.database import init_db
from core.scheduler import start_scheduler, stop_scheduler
from routers import auth, portfolio, rules, alerts, push, websocket

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    print("✅ Database ready")
    await start_scheduler()
    print("✅ Scheduler started")
    yield
    # Shutdown
    await stop_scheduler()

app = FastAPI(title="Finpop Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers
app.include_router(auth.router,      prefix="/api/auth",      tags=["Auth"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(rules.router,     prefix="/api/rules",     tags=["Rules"])
app.include_router(alerts.router,    prefix="/api/alerts",    tags=["Alerts"])
app.include_router(push.router,      prefix="/api/push",      tags=["Push"])
app.include_router(websocket.router, prefix="/ws",            tags=["WebSocket"])

@app.get("/")
async def root():
    return {"status": "ok", "service": "finpop-backend"}
