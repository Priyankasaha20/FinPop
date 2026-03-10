"""
routers/push.py
Expo push token registration.
The mobile app calls POST /api/push/register on startup
to give the backend its push token.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from core.database import upsert_push_token, get_push_tokens

router = APIRouter()


class TokenRequest(BaseModel):
    token: str


@router.post("/register")
async def register(req: TokenRequest):
    upsert_push_token(req.token)
    return {"status": "registered"}


@router.get("/tokens")
async def list_tokens():
    """Debug: list all registered push tokens."""
    return {"tokens": get_push_tokens()}
