"""
Helper utilities for the application
"""

import json
import re
import urllib.parse
from typing import Dict, Any, List, Optional

from app.config import PLATFORM_URLS, CATEGORY_PLATFORMS


def extract_json_from_response(text: str) -> Dict[str, Any]:
    """
    Extract JSON from AI response text
    Handles various formats: pure JSON, markdown code blocks, etc.
    """
    if not text:
        return {}
    
    # Try to find JSON in markdown code blocks
    json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    matches = re.findall(json_pattern, text)
    
    for match in matches:
        try:
            return json.loads(match.strip())
        except json.JSONDecodeError:
            continue
    
    # Try to find JSON object directly
    try:
        # Find the first { and last }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = text[start:end + 1]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    
    # Try parsing the entire text as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Return empty dict if all parsing fails
    return {}


def generate_shopping_links(
    search_terms: str,
    category: Optional[str] = None,
    custom_platforms: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Generate shopping links for a product search term
    
    Args:
        search_terms: Product search terms
        category: Optional category to determine relevant platforms
        custom_platforms: Optional custom list of platforms
    
    Returns:
        Dictionary of platform name to URL
    """
    if not search_terms:
        return {}
    
    # Encode search terms
    encoded_terms = urllib.parse.quote_plus(search_terms)
    
    # Determine which platforms to include
    if custom_platforms:
        platforms = custom_platforms
    elif category:
        cat_lower = category.lower().replace(" ", "_")
        platforms = CATEGORY_PLATFORMS.get(cat_lower, ["amazon", "flipkart", "google"])
    else:
        platforms = ["amazon", "flipkart", "google"]
    
    # Generate links
    links = {}
    for platform in platforms:
        if platform in PLATFORM_URLS:
            try:
                links[platform] = PLATFORM_URLS[platform].format(encoded_terms)
            except (KeyError, IndexError):
                continue
    
    return links


def format_currency(amount: float, currency: str = "₹") -> str:
    """Format amount as currency string"""
    return f"{currency}{amount:,.2f}"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers"""
    if denominator == 0:
        return default
    return numerator / denominator


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def calculate_percentage(part: float, whole: float) -> float:
    """Calculate percentage safely"""
    if whole == 0:
        return 0.0
    return (part / whole) * 100


def build_calculation_table(budget_breakdown: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build a calculation table from budget breakdown"""
    categories = {}
    
    for category in budget_breakdown:
        cat_name = category.get("category", "Misc")
        cat_allocation = category.get("allocation", 0)
        
        if cat_name not in categories:
            categories[cat_name] = {
                "category": cat_name,
                "allocation": cat_allocation,
                "items_count": 0,
                "total_cost": 0.0,
                "percentage_of_budget": 0.0
            }
        
        for item in category.get("items", []):
            categories[cat_name]["items_count"] += 1
            categories[cat_name]["total_cost"] += item.get("estimated_price", 0)
    
    return list(categories.values())


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe storage"""
    # Remove path separators and dangerous characters
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    filename = filename.replace(' ', '_')
    return filename[:100]  # Limit length