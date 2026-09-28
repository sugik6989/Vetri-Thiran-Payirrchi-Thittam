"""
Gemini AI integration utilities for PocketSmart AI
Handles all AI-powered recommendation generation
"""

import os
import json
import base64
from typing import Dict, Any, Optional, List
from io import BytesIO

import google.generativeai as genai
from PIL import Image
from fastapi import HTTPException

from app.config import GOOGLE_API_KEY
from app.models.schemas import (
    HomeBudgetInput,
    PartyBudgetInput,
    JewelryBudgetInput,
)
from app.utils.helpers import (
    extract_json_from_response,
    generate_shopping_links,
    build_calculation_table,
)

# Configure Gemini API
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None
    print("WARNING: Google API key not configured. AI features will not work.")


def usd_to_inr(amount_usd: float, exchange_rate: float = 83.0) -> float:
    """Convert USD amount to INR"""
    return amount_usd * exchange_rate


def _check_model_available():
    """Check if Gemini model is available"""
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="AI service unavailable. Please configure GOOGLE_API_KEY."
        )


def get_home_recommendations(budget_input: HomeBudgetInput) -> Dict[str, Any]:
    """
    Generate home interior recommendations within budget in INR
    """
    _check_model_available()
    
    try:
        # Build the prompt
        rooms = []
        if budget_input.has_living_room:
            rooms.append("Living Room")
        if budget_input.has_kitchen:
            rooms.append("Kitchen")
        if budget_input.has_bedroom:
            rooms.append("Bedroom")
        
        rooms_str = ", ".join(rooms) if rooms else "General"
        
        prompt = f"""
I need interior design product recommendations for a home in India with a total budget of ₹{budget_input.total_budget:.2f}.

Requirements:
- {budget_input.num_lights} lights/lighting fixtures
- {budget_input.num_fans} ceiling fans
- {budget_input.num_furniture} furniture pieces
- {budget_input.num_dining_tables} dining tables

Rooms to consider: {rooms_str}
Additional requirements: {budget_input.additional_requirements or "None"}

Please provide a detailed budget breakdown with product recommendations available in India.
Use Indian brands and pricing. Include search terms suitable for Indian shopping platforms.

IMPORTANT: Return ONLY valid JSON (no markdown, no code blocks) with this exact structure:
{{
    "total_budget": {budget_input.total_budget:.2f},
    "budget_breakdown": [
        {{
            "category": "lighting",
            "allocation": 0.0,
            "items": [
                {{
                    "name": "Product name",
                    "description": "Brief description",
                    "estimated_price": 0.0,
                    "quantity": 0,
                    "search_terms": "search terms for shopping"
                }}
            ]
        }}
    ],
    "remaining_budget": 0.0,
    "additional_suggestions": ["suggestion 1", "suggestion 2"]
}}

Ensure total costs stay within budget. Include search terms for each item to find on shopping websites like Flipkart, Amazon India, IKEA, etc.
"""
        
        # Generate response
        response = model.generate_content(prompt)
        result = extract_json_from_response(response.text)
        
        if not result:
            result = _get_fallback_home_recommendations(budget_input)
        
        # Add shopping links for each item
        for category in result.get("budget_breakdown", []):
            cat_name = category.get("category", "")
            for item in category.get("items", []):
                search_terms = item.get("search_terms", "")
                if search_terms:
                    item["shopping_links"] = generate_shopping_links(
                        search_terms, 
                        category=cat_name
                    )
        
        # Build calculation table
        result["calculation_table"] = build_calculation_table(
            result.get("budget_breakdown", [])
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_home_recommendations: {str(e)}")
        return _get_fallback_home_recommendations(budget_input)


def get_party_recommendations(budget_input: PartyBudgetInput) -> Dict[str, Any]:
    """
    Generate party planning recommendations within budget in INR
    """
    _check_model_available()
    
    try:
        prompt = f"""
I need party planning recommendations for India with a total budget of ₹{budget_input.total_budget:.2f}.

Party details:
- Type: {budget_input.party_type}
- Number of guests: {budget_input.num_guests}
- Venue type: {budget_input.venue_type or "Not specified"}
- Catering needed: {"Yes" if budget_input.needs_catering else "No"}
- Decoration needed: {"Yes" if budget_input.needs_decoration else "No"}
- Entertainment needed: {"Yes" if budget_input.needs_entertainment else "No"}
Additional requirements: {budget_input.additional_requirements or "None"}

Provide a detailed budget breakdown with specific recommendations available in India using INR prices.
Use Indian brands, services, and typical cost expectations.

IMPORTANT: Return ONLY valid JSON (no markdown, no code blocks) with this exact structure:
{{
    "total_budget": {budget_input.total_budget:.2f},
    "budget_breakdown": [
        {{
            "category": "venue",
            "allocation": 0.0,
            "items": [
                {{
                    "name": "Item/Service name",
                    "description": "Brief description",
                    "estimated_price": 0.0,
                    "quantity": 1,
                    "search_terms": "search terms"
                }}
            ]
        }}
    ],
    "remaining_budget": 0.0,
    "additional_suggestions": ["suggestion 1", "suggestion 2"]
}}

Categories to consider: venue, catering, decoration, entertainment, gifts, contingency.
Ensure total costs stay within budget. Include search terms for Indian websites.
"""
        
        response = model.generate_content(prompt)
        result = extract_json_from_response(response.text)
        
        if not result:
            result = _get_fallback_party_recommendations(budget_input)
        
        # Add shopping links for each item
        for category in result.get("budget_breakdown", []):
            cat_name = category.get("category", "").lower()
            for item in category.get("items", []):
                search_terms = item.get("search_terms", "")
                if search_terms:
                    item["shopping_links"] = generate_shopping_links(
                        search_terms,
                        category=cat_name
                    )
        
        # Build calculation table
        result["calculation_table_inr"] = build_calculation_table(
            result.get("budget_breakdown", [])
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_party_recommendations: {str(e)}")
        return _get_fallback_party_recommendations(budget_input)


def get_jewelry_recommendations(
    budget_input: JewelryBudgetInput,
    image_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate jewelry recommendations based on budget, occasion, and optional image
    """
    _check_model_available()
    
    try:
        base_prompt = f"""
I need jewelry recommendations for India with a total budget of ₹{budget_input.total_budget:.2f}.

Occasion: {budget_input.occasion}
Preferences: {budget_input.preferences or "Not specified"}
Additional requirements: {budget_input.additional_requirements or "None"}

Provide only India-relevant styles, availability, and price ranges in INR.
"""
        
        if image_path and os.path.exists(image_path):
            # Image-based analysis
            img = Image.open(image_path)
            
            prompt = base_prompt + """
            
An image of an outfit is uploaded. Suggest jewelry that complements it, considering color, design, and occasion appropriateness.

IMPORTANT: Return ONLY valid JSON (no markdown, no code blocks) with this exact structure:
{
    "outfit_analysis": {
        "colors": ["color1", "color2"],
        "style": "style description",
        "formality": "formal/casual/semi-formal"
    },
    "total_budget": 0.0,
    "jewelry_recommendations": [
        {
            "item_type": "type of jewelry",
            "description": "detailed description",
            "style": "style",
            "estimated_price": 0.0,
            "search_terms": "search terms"
        }
    ],
    "remaining_budget": 0.0,
    "styling_tips": ["tip 1", "tip 2"]
}

Make sure prices are in INR and stay within budget.
Include Indian-friendly search terms for shopping.
"""
            response = model.generate_content([prompt, img])
        else:
            # Text-only analysis
            prompt = base_prompt + """
            
IMPORTANT: Return ONLY valid JSON (no markdown, no code blocks) with this exact structure:
{
    "total_budget": 0.0,
    "jewelry_recommendations": [
        {
            "item_type": "type of jewelry",
            "description": "detailed description",
            "style": "style",
            "estimated_price": 0.0,
            "search_terms": "search terms"
        }
    ],
    "remaining_budget": 0.0,
    "styling_tips": ["tip 1", "tip 2"]
}

Keep prices in INR and relevant to Indian brands.
"""
            response = model.generate_content(prompt)
        
        result = extract_json_from_response(response.text)
        
        if not result:
            result = _get_fallback_jewelry_recommendations(budget_input)
        
        # Add shopping links for each jewelry item
        for item in result.get("jewelry_recommendations", []):
            search_terms = item.get("search_terms", "")
            if search_terms:
                item["shopping_links"] = generate_shopping_links(
                    search_terms,
                    category="jewelry"
                )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_jewelry_recommendations: {str(e)}")
        return _get_fallback_jewelry_recommendations(budget_input)


# ============== Fallback Functions ==============

def _get_fallback_home_recommendations(budget_input: HomeBudgetInput) -> Dict[str, Any]:
    """Fallback recommendations when AI is unavailable"""
    budget = budget_input.total_budget
    
    return {
        "total_budget": budget,
        "budget_breakdown": [
            {
                "category": "lighting",
                "allocation": budget * 0.2,
                "items": [
                    {
                        "name": "LED Bulbs (Warm White)",
                        "description": "Energy-efficient LED bulbs for general lighting",
                        "estimated_price": 200,
                        "quantity": max(1, budget_input.num_lights),
                        "search_terms": "LED bulb warm white",
                        "shopping_links": generate_shopping_links("LED bulb warm white", "lighting")
                    }
                ]
            },
            {
                "category": "fans",
                "allocation": budget * 0.25,
                "items": [
                    {
                        "name": "Ceiling Fan",
                        "description": "Basic functional ceiling fan",
                        "estimated_price": 1500,
                        "quantity": max(1, budget_input.num_fans),
                        "search_terms": "ceiling fan",
                        "shopping_links": generate_shopping_links("ceiling fan", "fans")
                    }
                ]
            },
            {
                "category": "furniture",
                "allocation": budget * 0.4,
                "items": [
                    {
                        "name": "Plastic Chair",
                        "description": "Stackable plastic chairs",
                        "estimated_price": 500,
                        "quantity": max(1, budget_input.num_furniture),
                        "search_terms": "plastic chair",
                        "shopping_links": generate_shopping_links("plastic chair", "furniture")
                    }
                ]
            }
        ],
        "remaining_budget": budget * 0.15,
        "additional_suggestions": [
            "Consider purchasing used furniture for cost savings",
            "Look for sales and discounts on online marketplaces",
            "Prioritize essential items and postpone non-essential purchases"
        ]
    }


def _get_fallback_party_recommendations(budget_input: PartyBudgetInput) -> Dict[str, Any]:
    """Fallback party recommendations when AI is unavailable"""
    budget = budget_input.total_budget
    
    return {
        "total_budget": budget,
        "budget_breakdown": [
            {
                "category": "catering",
                "allocation": budget * 0.4,
                "items": [
                    {
                        "name": "Catering Service",
                        "description": f"Catering for {budget_input.num_guests} guests",
                        "estimated_price": budget * 0.4,
                        "quantity": 1,
                        "search_terms": "party catering service",
                        "shopping_links": generate_shopping_links("party catering service", "catering")
                    }
                ]
            },
            {
                "category": "decoration",
                "allocation": budget * 0.3,
                "items": [
                    {
                        "name": "Decoration Package",
                        "description": "Party decoration items and setup",
                        "estimated_price": budget * 0.3,
                        "quantity": 1,
                        "search_terms": "party decoration",
                        "shopping_links": generate_shopping_links("party decoration", "decoration")
                    }
                ]
            },
            {
                "category": "entertainment",
                "allocation": budget * 0.2,
                "items": [
                    {
                        "name": "Entertainment",
                        "description": "Music and entertainment setup",
                        "estimated_price": budget * 0.2,
                        "quantity": 1,
                        "search_terms": "party entertainment",
                        "shopping_links": generate_shopping_links("party entertainment", "entertainment")
                    }
                ]
            }
        ],
        "remaining_budget": budget * 0.1,
        "additional_suggestions": [
            "Consider DIY decorations to save costs",
            "Book venues in advance for better rates",
            "Create a playlist instead of hiring a DJ"
        ]
    }


def _get_fallback_jewelry_recommendations(budget_input: JewelryBudgetInput) -> Dict[str, Any]:
    """Fallback jewelry recommendations when AI is unavailable"""
    budget = budget_input.total_budget
    
    return {
        "total_budget": budget,
        "jewelry_recommendations": [
            {
                "item_type": "Necklace",
                "description": "Elegant necklace suitable for the occasion",
                "style": "Classic",
                "estimated_price": budget * 0.5,
                "search_terms": f"{budget_input.occasion} necklace jewelry",
                "shopping_links": generate_shopping_links(
                    f"{budget_input.occasion} necklace", "jewelry"
                )
            },
            {
                "item_type": "Earrings",
                "description": "Matching earrings",
                "style": "Contemporary",
                "estimated_price": budget * 0.3,
                "search_terms": f"{budget_input.occasion} earrings",
                "shopping_links": generate_shopping_links(
                    f"{budget_input.occasion} earrings", "jewelry"
                )
            }
        ],
        "remaining_budget": budget * 0.2,
        "styling_tips": [
            "Match jewelry with your outfit's color palette",
            "Consider the neckline when choosing necklaces",
            "Keep it minimal for daytime events"
        ]
    }