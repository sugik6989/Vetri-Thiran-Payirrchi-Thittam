"""
Home Interior Budget Planner routes

Routes:
    GET  /home_planner  -> serve HTML form
    POST /home-budget   -> generate recommendations (calls service layer)
"""

from datetime import datetime
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any

from app.config import TEMPLATES_DIR
from app.models.schemas import HomeBudgetInput, UserInDB
from app.services.recommendation_service import (
    generate_home_plan,
    summarize_result,
)
from app.utils.auth_utils import get_current_active_user, active_sessions

router = APIRouter(tags=["Home Planner"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Shared in-memory recommendation history
# NOTE: keyed by username, list of dict items
user_recommendations: Dict[str, list] = {}


# ==============================================================
# HTML Page
# ==============================================================

@router.get("/home_planner", response_class=HTMLResponse)
async def home_planner_page(
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Home budget planner page."""
    return templates.TemplateResponse(
        "home_planner.html",
        {"request": request, "user": current_user},
    )


# ==============================================================
# API Endpoint
# ==============================================================

@router.post("/home-budget")
async def plan_home_budget(
    budget_input: HomeBudgetInput,
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Generate home budget recommendations via service layer."""
    # --- Store last input in session data ---
    if current_user.username in active_sessions:
        active_sessions[current_user.username].user_data[
            "last_home_budget"
        ] = {
            "timestamp": datetime.utcnow().isoformat(),
            "budget": budget_input.total_budget,
            "requirements": {
                "lights": budget_input.num_lights,
                "fans": budget_input.num_fans,
                "furniture": budget_input.num_furniture,
                "dining_tables": budget_input.num_dining_tables,
            },
        }

    # --- Call service layer ---
    envelope = generate_home_plan(budget_input)

    if not envelope.get("success"):
        # Fall through to error propagation via response body
        # The frontend handles `success: false` gracefully.
        return envelope

    # --- Save to history ---
    save_to_history(
        username=current_user.username,
        recommendation_type="home",
        input_data=budget_input.model_dump(),
        result=envelope["data"],
    )

    # Return just the data payload (backward compatible with the
    # existing frontend that expects the flat recommendation object).
    return envelope["data"]


# ==============================================================
# Shared History Helpers
# ==============================================================

def save_to_history(
    username: str,
    recommendation_type: str,
    input_data: dict,
    result: dict,
):
    """Save a recommendation to the user's in-memory history."""
    import uuid

    if username not in user_recommendations:
        user_recommendations[username] = []

    history_item = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow(),
        "type": recommendation_type,
        "input": input_data,
        "result": result,
        "summary": summarize_result(recommendation_type, result),
    }

    user_recommendations[username].insert(0, history_item)

    # Cap history to last 50 entries per user
    user_recommendations[username] = user_recommendations[username][:50]