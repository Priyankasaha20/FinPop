"""
routers/rules.py
Rule management:
  - POST /parse     → plain English → structured JSON via Claude
  - POST /          → save a rule (works for both NL-parsed + preset)
  - GET  /          → list all rules
  - DELETE /{id}    → delete a rule
  - POST /{id}/reset → re-arm a triggered rule
  - POST /{id}/test  → dry-run against live quote
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal
import os

from core.database import (
    save_rule, get_all_rules, get_rule_by_id,
    delete_rule, reset_rule
)
from core.kite import fetch_quote
from core.rule_engine import parse_nl_rule

router = APIRouter()

# Preset condition options the mobile UI can display as a picker
PRESET_CONDITIONS = [
    {"id": "pct_change_down", "label": "% Drop from open"},
    {"id": "pct_change_up",   "label": "% Rise from open"},
    {"id": "pct_change_down_prev", "label": "% Drop from prev close"},
    {"id": "pct_change_up_prev",   "label": "% Rise from prev close"},
    {"id": "above",           "label": "Price goes above ₹"},
    {"id": "below",           "label": "Price goes below ₹"},
]


class NLRequest(BaseModel):
    text: str


class RuleCreate(BaseModel):
    instrument: str
    condition:  str
    threshold:  float
    timeframe:  Literal["from_open", "from_prev_close", "absolute"] = "absolute"
    description: str
    source:     Literal["nl", "preset"] = "preset"


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/preset-conditions")
async def preset_conditions():
    """Returns the list of preset condition types for the UI picker."""
    return PRESET_CONDITIONS


@router.post("/parse")
async def parse_rule(req: NLRequest):
    """
    Convert plain English to a structured rule JSON using Claude.
    The mobile app shows this as a preview before the user saves.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")
    try:
        result = await parse_nl_rule(req.text, api_key)
        result["source"] = "nl"
        return result
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not parse rule: {e}")


@router.post("")
async def create_rule(rule: RuleCreate):
    """Save a rule (whether NL-parsed or from preset UI)."""
    # Normalise pct_change_down_prev → condition + timeframe
    condition = rule.condition
    timeframe = rule.timeframe
    if condition == "pct_change_down_prev":
        condition = "pct_change_down"
        timeframe = "from_prev_close"
    elif condition == "pct_change_up_prev":
        condition = "pct_change_up"
        timeframe = "from_prev_close"

    rule_id = save_rule({
        "instrument":  rule.instrument,
        "condition":   condition,
        "threshold":   rule.threshold,
        "timeframe":   timeframe,
        "description": rule.description,
        "source":      rule.source,
    })
    return {"rule_id": rule_id, "status": "active"}


@router.get("")
async def list_rules():
    return get_all_rules()


@router.delete("/{rule_id}")
async def remove_rule(rule_id: int):
    delete_rule(rule_id)
    return {"status": "deleted"}


@router.post("/{rule_id}/reset")
async def rearm_rule(rule_id: int):
    """Re-arm a triggered rule so it can fire again."""
    reset_rule(rule_id)
    return {"status": "reset"}


@router.post("/{rule_id}/test")
async def test_rule(rule_id: int):
    """
    Dry-run: check if the rule would fire right now
    without actually triggering it.
    """
    rule = get_rule_by_id(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    instrument = rule["instrument"]
    try:
        quotes    = fetch_quote([instrument])
        q         = quotes.get(instrument, {})
        last_price = q.get("last_price", 0)
        ohlc      = q.get("ohlc", {})

        condition  = rule["condition"]
        threshold  = float(rule["threshold"])
        timeframe  = rule["timeframe"]

        ref = None
        if timeframe == "from_open":
            ref = ohlc.get("open")
        elif timeframe == "from_prev_close":
            ref = ohlc.get("close")

        would_trigger = False
        if condition == "above":
            would_trigger = last_price > threshold
        elif condition == "below":
            would_trigger = last_price < threshold
        elif condition == "pct_change_down" and ref:
            would_trigger = ((ref - last_price) / ref * 100) >= threshold
        elif condition == "pct_change_up" and ref:
            would_trigger = ((last_price - ref) / ref * 100) >= threshold

        return {
            "rule_id":       rule_id,
            "would_trigger": would_trigger,
            "current_price": last_price,
            "reference_price": ref,
            "description":   rule["description"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
