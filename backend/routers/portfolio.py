"""
routers/portfolio.py
REST endpoints for portfolio data.
The mobile app calls these on initial load; live updates come via WebSocket.
"""

from fastapi import APIRouter
from core.kite import fetch_holdings, fetch_orders, fetch_margins, fetch_quote

router = APIRouter()


@router.get("/holdings")
async def holdings():
    """
    All long-term holdings in the user's demat account.
    Returns instrument, qty, avg price, LTP, P&L.
    """
    return fetch_holdings()


@router.get("/orders")
async def orders():
    """
    Today's order history — all placed orders with status.
    """
    return fetch_orders()


@router.get("/margins")
async def margins():
    """
    Account balance and margin details for equity + commodity segments.
    """
    return fetch_margins()


@router.get("/snapshot")
async def snapshot():
    """
    Single endpoint that returns everything — used for initial app load.
    """
    return {
        "holdings": fetch_holdings(),
        "orders":   fetch_orders(),
        "margins":  fetch_margins(),
    }


@router.get("/quote")
async def quote(instruments: str):
    """
    Live quote for one or more instruments.
    Pass comma-separated: ?instruments=NSE:NIFTY 50,NSE:RELIANCE
    """
    inst_list = [i.strip() for i in instruments.split(",")]
    return fetch_quote(inst_list)
