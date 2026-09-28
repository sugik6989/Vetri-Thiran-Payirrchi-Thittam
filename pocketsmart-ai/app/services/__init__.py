"""
Services package for PocketSmart AI.

Exposes:
- gemini_utils: low-level AI calls
- recommendation_service: high-level business logic over AI
"""

from .gemini_utils import (
    get_home_recommendations,
    get_party_recommendations,
    get_jewelry_recommendations,
    usd_to_inr,
)

from .recommendation_service import (
    generate_home_plan,
    generate_party_plan,
    generate_jewelry_plan,
    summarize_result,
)

__all__ = [
    # Low-level AI
    "get_home_recommendations",
    "get_party_recommendations",
    "get_jewelry_recommendations",
    "usd_to_inr",
    # High-level service
    "generate_home_plan",
    "generate_party_plan",
    "generate_jewelry_plan",
    "summarize_result",
]