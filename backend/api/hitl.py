"""
HITL API Routes — Phase 4

API endpoints for Human-in-the-Loop clarification cards.

Endpoints:
- GET /api/hitl/pending - Get pending clarification cards
- POST /api/hitl/respond - Submit response to a card
- GET /api/hitl/feedback - Get feedback history for learning
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from backend.engine.hitl_manager import (
    get_hitl_manager,
    ClarificationResponse,
)


router = APIRouter(prefix="/api/hitl", tags=["HITL"])


# ─── Request/Response Models ─────────────────────────────────────────────────

class ClarificationResponseRequest(BaseModel):
    """Request body for submitting a clarification response."""
    card_id: str
    selected_option: Optional[str] = None
    custom_instruction: str = ""


class ClarificationCardResponse(BaseModel):
    """Response model for a clarification card."""
    id: str
    agent: str
    title: str
    description: str
    context: str
    choices: List[str]
    confidence: float
    timestamp: str
    metadata: Dict[str, Any] = {}


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/pending")
async def get_pending_cards() -> Dict[str, Any]:
    """
    Get all pending clarification cards.
    
    Returns:
        {"cards": [...], "count": int}
    """
    manager = get_hitl_manager()
    cards = manager.get_pending_cards()
    return {
        "cards": cards,
        "count": len(cards),
    }


@router.post("/respond")
async def respond_to_card(request: ClarificationResponseRequest) -> Dict[str, Any]:
    """
    Submit a response to a clarification card.
    
    This unblocks the engine from AWAITING_HUMAN state.
    
    Args:
        request: Card ID and user's response
        
    Returns:
        {"success": bool, "message": str}
    """
    manager = get_hitl_manager()
    
    response = ClarificationResponse(
        card_id=request.card_id,
        selected_option=request.selected_option,
        custom_instruction=request.custom_instruction,
    )
    
    success = manager.respond(request.card_id, response)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Card {request.card_id} not found or already resolved"
        )
    
    return {
        "success": True,
        "message": "Response recorded, agent will resume with your guidance",
        "card_id": request.card_id,
    }


@router.get("/feedback")
async def get_feedback_history() -> Dict[str, Any]:
    """
    Get feedback history for prompt_optimizer learning.
    
    Returns:
        {"entries": [...], "count": int}
    """
    manager = get_hitl_manager()
    entries = manager.get_feedback_history()
    return {
        "entries": entries,
        "count": len(entries),
    }


@router.delete("/pending/{card_id}")
async def dismiss_card(card_id: str) -> Dict[str, Any]:
    """
    Dismiss a pending card without response (timeout/abort).
    
    Args:
        card_id: ID of card to dismiss
        
    Returns:
        {"success": bool}
    """
    manager = get_hitl_manager()
    
    if card_id in manager.pending_cards:
        del manager.pending_cards[card_id]
        return {"success": True}
    
    raise HTTPException(status_code=404, detail="Card not found")
