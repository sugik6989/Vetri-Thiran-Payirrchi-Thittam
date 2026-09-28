"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============== User Schemas ==============

class UserRegister(BaseModel):
    """User registration input schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """User login input schema"""
    username: str
    password: str


class UserInDB(BaseModel):
    """User model stored in database"""
    username: str
    email: str
    full_name: Optional[str] = None
    hashed_password: str
    disabled: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Token(BaseModel):
    """JWT token response schema"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload schema"""
    username: Optional[str] = None


# ============== Budget Input Schemas ==============

class HomeBudgetInput(BaseModel):
    """Home interior budget planner input schema"""
    total_budget: float = Field(..., gt=0, description="Total budget in INR")
    num_lights: int = Field(default=0, ge=0, description="Number of lights needed")
    num_fans: int = Field(default=0, ge=0, description="Number of ceiling fans needed")
    num_furniture: int = Field(default=0, ge=0, description="Number of furniture pieces")
    num_dining_tables: int = Field(default=0, ge=0, description="Number of dining tables")
    has_living_room: bool = Field(default=True)
    has_kitchen: bool = Field(default=False)
    has_bedroom: bool = Field(default=False)
    additional_requirements: Optional[str] = None


class PartyBudgetInput(BaseModel):
    """Party budget planner input schema"""
    total_budget: float = Field(..., gt=0, description="Total budget in INR")
    party_type: str = Field(..., description="Type of party (birthday, wedding, corporate, etc.)")
    num_guests: int = Field(..., gt=0, description="Number of guests")
    venue_type: Optional[str] = Field(default=None, description="Type of venue")
    needs_catering: bool = Field(default=True)
    needs_decoration: bool = Field(default=True)
    needs_entertainment: bool = Field(default=False)
    additional_requirements: Optional[str] = None


class JewelryBudgetInput(BaseModel):
    """Jewelry budget planner input schema"""
    total_budget: float = Field(..., gt=0, description="Total budget in INR")
    occasion: str = Field(..., description="Occasion (wedding, birthday, anniversary, etc.)")
    preferences: Optional[str] = Field(default=None, description="Style preferences")
    additional_requirements: Optional[str] = None


# ============== Recommendation Response Schemas ==============

class BudgetItem(BaseModel):
    """Individual item in budget breakdown"""
    name: str
    description: str
    estimated_price: float
    quantity: int = 1
    search_terms: str
    shopping_links: Optional[Dict[str, str]] = None


class BudgetCategory(BaseModel):
    """Category in budget breakdown"""
    category: str
    allocation: float
    items: List[BudgetItem]


class BudgetRecommendation(BaseModel):
    """Complete budget recommendation response"""
    total_budget: float
    budget_breakdown: List[BudgetCategory]
    remaining_budget: float
    additional_suggestions: List[str] = []
    calculation_table: Optional[List[Dict[str, Any]]] = None


class JewelryRecommendation(BaseModel):
    """Jewelry recommendation response"""
    total_budget: float
    jewelry_recommendations: List[Dict[str, Any]]
    remaining_budget: float
    styling_tips: List[str] = []
    outfit_analysis: Optional[Dict[str, Any]] = None


class HistoryItem(BaseModel):
    """History item schema"""
    id: str
    timestamp: datetime
    type: str
    input: Dict[str, Any]
    summary: str