"""
routers/auth.py
Kite Connect OAuth flow.

Step 1: GET  /api/auth/login-url?api_key=xxx  → returns redirect URL
Step 2: User logs in on Zerodha → redirected back with ?request_token=xxx
Step 3: POST /api/auth/token  → exchanges token, saves session
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.kite import create_kite_session, get_login_url, get_kite
from core.database import get_session

router = APIRouter()


class TokenRequest(BaseModel):
    api_key:       str
    api_secret:    str
    request_token: str


@router.get("/login-url")
async def login_url(api_key: str):
    """
    Returns the Zerodha OAuth URL.
    Open this in a browser / in-app WebView.
    After login, Zerodha redirects to your redirect_url with ?request_token=xxx
    """
    url = get_login_url(api_key)
    return {"url": url}


@router.post("/token")
async def exchange_token(req: TokenRequest):
    """
    Exchange request_token for access_token.
    Call this once after the OAuth redirect.
    """
    try:
        data = create_kite_session(req.api_key, req.api_secret, req.request_token)
        return {
            "status":    "authenticated",
            "user_id":   data.get("user_id"),
            "user_name": data.get("user_name"),
            "email":     data.get("email"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
async def auth_status():
    """Check if a Kite session exists."""
    session = get_session()
    if not session:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "user_name": session.get("user_name"),
        "user_id":   session.get("user_id"),
        "logged_in_at": session.get("logged_in_at"),
    }


@router.delete("/logout")
async def logout():
    """Invalidate the current Kite session."""
    try:
        kite = get_kite()
        if kite:
            kite.invalidate_access_token()
    except Exception:
        pass  # Token may already be expired

    from core.database import get_conn
    with get_conn() as conn:
        conn.execute("DELETE FROM kite_session")
        conn.commit()

    return {"status": "logged_out"}
