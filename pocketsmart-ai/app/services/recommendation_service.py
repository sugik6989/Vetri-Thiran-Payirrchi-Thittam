"""
Recommendation Service Layer for PocketSmart AI

This module provides a high-level service abstraction over the raw Gemini
utility functions. It handles:
  - Input normalization (currency, defaults)
  - Response envelope standardization
  - Fallback handling when AI returns incomplete data
  - Logging for debugging and monitoring

The API route handlers should call functions in THIS module rather than
calling gemini_utils directly, keeping routes thin and testable.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from app.models.schemas import (
    HomeBudgetInput,
    PartyBudgetInput,
    JewelryBudgetInput,
)
from app.services.gemini_utils import (
    get_home_recommendations,
    get_party_recommendations,
    get_jewelry_recommendations,
)
from app.utils.helpers import (
    generate_shopping_links,
    build_calculation_table,
    format_currency,
)

logger = logging.getLogger(__name__)


# ==============================================================
# Response Envelope Helpers
# ==============================================================

def _build_response_envelope(
    planner_type: str,
    data: Dict[str, Any],
    success: bool = True,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Wrap recommendation output in a standard envelope.
    This makes frontend parsing consistent across planners.
    """
    return {
        "success": success,
        "planner_type": planner_type,
        "generated_at": datetime.utcnow().isoformat(),
        "error": error,
        "data": data if success else {},
    }


def _ensure_shopping_links(result: Dict[str, Any], category: str) -> Dict[str, Any]:
    """
    Ensure every item in a budget breakdown has shopping links.
    This is a safety net in case the AI forgot to include search terms.
    """
    for cat in result.get("budget_breakdown", []):
        cat_name = cat.get("category", category)
        for item in cat.get("items", []):
            if not item.get("shopping_links"):
                terms = item.get("search_terms") or item.get("name", "")
                if terms:
                    item["shopping_links"] = generate_shopping_links(
                        terms, category=cat_name
                    )
    return result


def _ensure_calculation_table(
    result: Dict[str, Any], table_key: str = "calculation_table"
) -> Dict[str, Any]:
    """Ensure calculation table exists for reporting."""
    if table_key not in result:
        result[table_key] = build_calculation_table(
            result.get("budget_breakdown", [])
        )
    return result


# ==============================================================
# Home Planner Service
# ==============================================================

def generate_home_plan(budget_input: HomeBudgetInput) -> Dict[str, Any]:
    """
    Generate a home interior recommendation plan.

    Args:
        budget_input: Validated HomeBudgetInput Pydantic model

    Returns:
        Standardized response envelope with the plan under 'data'
    """
    logger.info(
        f"Generating home plan | budget={budget_input.total_budget} "
        f"lights={budget_input.num_lights} fans={budget_input.num_fans}"
    )

    try:
        raw = get_home_recommendations(budget_input)

        # Safety nets
        raw = _ensure_shopping_links(raw, category="furniture")
        raw = _ensure_calculation_table(raw, table_key="calculation_table")

        # Ensure budget values exist
        raw.setdefault("total_budget", budget_input.total_budget)
        raw.setdefault(
            "remaining_budget",
            budget_input.total_budget
            - sum(
                cat.get("allocation", 0)
                for cat in raw.get("budget_breakdown", [])
            ),
        )

        return _build_response_envelope("home", raw)

    except Exception as exc:
        logger.exception("Home plan generation failed")
        return _build_response_envelope(
            "home", {}, success=False, error=str(exc)
        )


# ==============================================================
# Party Planner Service
# ==============================================================

def generate_party_plan(budget_input: PartyBudgetInput) -> Dict[str, Any]:
    """
    Generate a party planning recommendation plan.

    Args:
        budget_input: Validated PartyBudgetInput Pydantic model

    Returns:
        Standardized response envelope with the plan under 'data'
    """
    logger.info(
        f"Generating party plan | type={budget_input.party_type} "
        f"guests={budget_input.num_guests} budget={budget_input.total_budget}"
    )

    try:
        raw = get_party_recommendations(budget_input)

        # Safety nets
        raw = _ensure_shopping_links(raw, category="catering")
        raw = _ensure_calculation_table(raw, table_key="calculation_table_inr")

        raw.setdefault("total_budget", budget_input.total_budget)
        raw.setdefault(
            "remaining_budget",
            budget_input.total_budget
            - sum(
                cat.get("allocation", 0)
                for cat in raw.get("budget_breakdown", [])
            ),
        )

        return _build_response_envelope("party", raw)

    except Exception as exc:
        logger.exception("Party plan generation failed")
        return _build_response_envelope(
            "party", {}, success=False, error=str(exc)
        )


# ==============================================================
# Jewelry Planner Service
# ==============================================================

def generate_jewelry_plan(
    budget_input: JewelryBudgetInput,
    image_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a jewelry recommendation plan (optionally multimodal).

    Args:
        budget_input: Validated JewelryBudgetInput Pydantic model
        image_path: Optional path to uploaded outfit image

    Returns:
        Standardized response envelope with the plan under 'data'
    """
    logger.info(
        f"Generating jewelry plan | occasion={budget_input.occasion} "
        f"budget={budget_input.total_budget} "
        f"image={'yes' if image_path else 'no'}"
    )

    try:
        raw = get_jewelry_recommendations(budget_input, image_path)

        # Jewelry items use a different key than 'budget_breakdown'
        for item in raw.get("jewelry_recommendations", []):
            if not item.get("shopping_links"):
                terms = item.get("search_terms") or item.get("item_type", "")
                if terms:
                    item["shopping_links"] = generate_shopping_links(
                        terms, category="jewelry"
                    )

        raw.setdefault("total_budget", budget_input.total_budget)
        raw.setdefault("remaining_budget", 0.0)
        raw.setdefault("styling_tips", [])

        return _build_response_envelope("jewelry", raw)

    except Exception as exc:
        logger.exception("Jewelry plan generation failed")
        return _build_response_envelope(
            "jewelry", {}, success=False, error=str(exc)
        )


# ==============================================================
# Summary Helpers (used by history route)
# ==============================================================

def summarize_result(planner_type: str, result: Dict[str, Any]) -> str:
    """
    Produce a short human-readable summary of a recommendation result.
    Used by the history view.
    """
    data = result.get("data", result)  # support both envelopes
    budget = data.get("total_budget", 0)
    remaining = data.get("remaining_budget", 0)

    if planner_type == "home":
        return f"Home Budget: {format_currency(budget)} | Remaining: {format_currency(remaining)}"
    if planner_type == "party":
        return f"Party Budget: {format_currency(budget)} | Remaining: {format_currency(remaining)}"
    if planner_type == "jewelry":
        return f"Jewelry Budget: {format_currency(budget)} | Remaining: {format_currency(remaining)}"
    return f"Budget: {format_currency(budget)}"