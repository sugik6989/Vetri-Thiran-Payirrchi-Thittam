"""
Configuration module for PocketSmart AI
Loads environment variables and provides application settings
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Application Settings
APP_NAME = os.getenv("APP_NAME", "PocketSmart AI")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# Security Settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Google Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

# Directory Settings
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
UPLOADS_DIR = STATIC_DIR / "uploads"

# Ensure uploads directory exists
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Platform URLs for shopping links
PLATFORM_URLS = {
    "amazon": "https://www.amazon.in/s?k={}",
    "flipkart": "https://www.flipkart.com/search?q={}",
    "ikea": "https://www.ikea.com/in/en/search/?q={}",
    "myntra": "https://www.myntra.com/{}",
    "ajio": "https://www.ajio.com/search/?text={}",
    "meesho": "https://www.meesho.com/search?q={}",
    "swiggy": "https://www.swiggy.com/search?query={}",
    "zomato": "https://www.zomato.com/search?q={}",
    "bigbasket": "https://www.bigbasket.com/ps/?q={}",
    "bookmyshow": "https://in.bookmyshow.com/search?q={}",
    "oyorooms": "https://www.oyorooms.com/search?location={}",
    "makemytrip": "https://www.makemytrip.com/hotels/hotel-listing/?searchText={}",
    "nobroker": "https://www.nobroker.in/property/search?searchTerms={}",
    "google": "https://www.google.com/search?q={}",
    "bluestone": "https://www.bluestone.com/search.html?query={}",
    "tanishq": "https://www.tanishq.co.in/search?q={}",
    "caratlane": "https://www.caratlane.com/search?q={}",
    "melorra": "https://www.melorra.com/search?q={}",
    "booking": "https://www.booking.com/search.html?ss={}",
}

# Category to platform mapping
CATEGORY_PLATFORMS = {
    "venue": ["google", "booking", "makemytrip", "oyorooms", "nobroker"],
    "catering": ["swiggy", "zomato", "flipkart"],
    "food": ["swiggy", "zomato", "bigbasket", "amazon", "flipkart"],
    "drinks": ["swiggy", "zomato", "bigbasket", "amazon", "flipkart"],
    "decoration": ["amazon", "flipkart", "meesho", "myntra"],
    "entertainment": ["bookmyshow", "amazon", "flipkart"],
    "gifts": ["amazon", "flipkart", "myntra", "meesho"],
    "photography": ["google", "amazon", "flipkart"],
    "music": ["amazon", "flipkart", "bookmyshow"],
    "games": ["amazon", "flipkart"],
    "accessories": ["amazon", "flipkart", "myntra", "meesho"],
    "transportation": ["makemytrip", "google"],
    "return_gifts": ["amazon", "flipkart", "myntra", "meesho"],
    "lighting": ["amazon", "flipkart", "ikea", "myntra", "ajio"],
    "furniture": ["amazon", "flipkart", "ikea", "myntra"],
    "ceiling_fans": ["amazon", "flipkart", "ikea"],
    "jewelry": ["amazon", "flipkart", "bluestone", "tanishq", "caratlane", "melorra", "meesho"],
}