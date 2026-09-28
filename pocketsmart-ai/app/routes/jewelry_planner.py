"""
Jewelry Budget Planner routes

Routes:
    GET  /jewelry_planner  -> serve HTML form (supports image upload)
    POST /jewelry-budget   -> generate recommendations (calls service layer)
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import (
    APIRouter,
    Request,
    Depends,
    File,
    UploadFile,
    Form,
    HTTPException,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import TEMPLATES_DIR, UPLOADS_DIR
from app.models.schemas import JewelryBudgetInput, UserInDB
from app.services.recommendation_service import generate_jewelry_plan
from app.utils.auth_utils import get_current_active_user, active_sessions
from app.routes.home_planner import save_to_history

router = APIRouter(tags=["Jewelry Planner"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ==============================================================
# HTML Page
# ==============================================================

@router.get("/jewelry_planner", response_class=HTMLResponse)
async def jewelry_planner_page(
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Jewelry budget planner page."""
    return templates.TemplateResponse(
        "jewelry_planner.html",
        {"request": request, "user": current_user},
    )


# ==============================================================
# API Endpoint (multipart/form-data — supports image upload)
# ==============================================================

@router.post("/jewelry-budget")
async def plan_jewelry_budget(
    request: Request,
    total_budget: float = Form(...),
    occasion: str = Form(...),
    preferences: Optional[str] = Form(None),
    additional_requirements: Optional[str] = Form(None),
    outfit_image: Optional[UploadFile] = File(None),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Generate jewelry budget recommendations via service layer."""
    # --- Handle optional image upload ---
    image_path: Optional[str] = None
    if outfit_image and outfit_image.filename:
        allowed_types = {
            "image/jpeg",
            "image/png",
            "image/jpg",
            "image/webp",
        }
        if outfit_image.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Invalid image format. Use JPEG, PNG, or WebP.",
            )

        file_ext = outfit_image.filename.rsplit(".", 1)[-1].lower()
        filename = f"{uuid.uuid4()}.{file_ext}"
        image_path = str(UPLOADS_DIR / filename)

        content = await outfit_image.read()
        with open(image_path, "wb") as fh:
            fh.write(content)

    # --- Build validated input ---
    budget_input = JewelryBudgetInput(
        total_budget=total_budget,
        occasion=occasion,
        preferences=preferences,
        additional_requirements=additional_requirements,
    )

    # --- Session tracking ---
    if current_user.username in active_sessions:
        active_sessions[current_user.username].user_data[
            "last_jewelry_budget"
        ] = {
            "timestamp": datetime.utcnow().isoformat(),
            "budget": total_budget,
            "occasion": occasion,
            "had_image": image_path is not None,
        }

    # --- Call service layer ---
    envelope = generate_jewelry_plan(budget_input, image_path)

    if not envelope.get("success"):
        return envelope

    # --- Save to history ---
    input_payload = budget_input.model_dump()
    input_payload["had_image"] = image_path is not None

    save_to_history(
        username=current_user.username,
        recommendation_type="jewelry",
        input_data=input_payload,
        result=envelope["data"],
    )

    return envelope["data"]