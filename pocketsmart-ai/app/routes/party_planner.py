"""
Party Budget Planner routes

Routes:
    GET  /party_planner  -> serve HTML form
    POST /party-budget   -> generate recommendations (calls service layer)
"""

from datetime import datetime
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR
from app.models.schemas import PartyBudgetInput, UserInDB
from app.services.recommendation_service import generate_party_plan
from app.utils.auth_utils import get_current_active_user, active_sessions
from app.routes.home_planner import save_to_history

router = APIRouter(tags=["Party Planner"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ==============================================================
# HTML Page
# ==============================================================

@router.get("/party_planner", response_class=HTMLResponse)
async def party_planner_page(
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Party budget planner page."""
    return templates.TemplateResponse(
        "party_planner.html",
        {"request": request, "user": current_user},
    )


# ==============================================================
# API Endpoint
# ==============================================================

@router.post("/party-budget")
async def plan_party_budget(
    budget_input: PartyBudgetInput,
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Generate party budget recommendations via service layer."""
    # --- Session tracking ---
    if current_user.username in active_sessions:
        active_sessions[current_user.username].user_data[
            "last_party_budget"
        ] = {
            "timestamp": datetime.utcnow().isoformat(),
            "budget": budget_input.total_budget,
            "party_type": budget_input.party_type,
            "guests": budget_input.num_guests,
        }

    # --- Call service layer ---
    envelope = generate_party_plan(budget_input)

    if not envelope.get("success"):
        return envelope

    # --- Save to history ---
    save_to_history(
        username=current_user.username,
        recommendation_type="party",
        input_data=budget_input.model_dump(),
        result=envelope["data"],
    )

    return envelope["data"]