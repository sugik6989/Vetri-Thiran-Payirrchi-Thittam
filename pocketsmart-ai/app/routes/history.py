"""
History routes — view and re-open past recommendations.

Routes:
    GET /history                                  -> HTML page
    GET /history-data                             -> list of items
    GET /recommendation-details/{recommendation_id} -> full detail
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.models.schemas import UserInDB
from app.utils.auth_utils import get_current_active_user
from app.routes.home_planner import user_recommendations
from app.services.recommendation_service import summarize_result

router = APIRouter(tags=["History"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ==============================================================
# HTML Page
# ==============================================================

@router.get("/history", response_class=HTMLResponse)
async def history_page(
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """History page to view past recommendations."""
    return templates.TemplateResponse(
        "history.html",
        {"request": request, "user": current_user},
    )


# ==============================================================
# API: List history items
# ==============================================================

@router.get("/history-data")
async def get_history_data(
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Return the user's recommendation history (newest first)."""
    items = user_recommendations.get(current_user.username, [])

    if not items:
        return {"history": []}

    # Already stored newest-first (insert at index 0) but sort
    # defensively in case of future refactor.
    items_sorted = sorted(
        items, key=lambda x: x["timestamp"], reverse=True
    )

    return {
        "history": [
            {
                "id": item["id"],
                "timestamp": item["timestamp"].isoformat(),
                "type": item["type"],
                "input": item["input"],
                "summary": item.get("summary")
                or summarize_result(item["type"], item["result"]),
            }
            for item in items_sorted
        ]
    }


# ==============================================================
# API: Full details for a single recommendation
# ==============================================================

@router.get("/recommendation-details/{recommendation_id}")
async def get_recommendation_details(
    recommendation_id: str,
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Return full details of a specific recommendation."""
    items = user_recommendations.get(current_user.username, [])

    if not items:
        raise HTTPException(
            status_code=404, detail="No recommendations found"
        )

    for item in items:
        if item["id"] == recommendation_id:
            return {
                "id": item["id"],
                "timestamp": item["timestamp"].isoformat(),
                "type": item["type"],
                "input": item["input"],
                "full_result": item["result"],
            }

    raise HTTPException(
        status_code=404, detail="Recommendation not found"
    )