"""
User database model (in-memory implementation)
"""

from datetime import datetime
from typing import Dict, Optional
from app.models.schemas import UserInDB


class UserDatabase:
    """In-memory user database"""
    
    def __init__(self):
        self._users: Dict[str, UserInDB] = {}
        self._initialize_default_user()
    
    def _initialize_default_user(self):
        """Create a default demo user"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        demo_user = UserInDB(
            username="demo",
            email="demo@pocketsmart.ai",
            full_name="Demo User",
            hashed_password=pwd_context.hash("demo123"),
            created_at=datetime.utcnow()
        )
        self._users["demo"] = demo_user
    
    def get_user(self, username: str) -> Optional[UserInDB]:
        """Get user by username"""
        return self._users.get(username)
    
    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        for user in self._users.values():
            if user.email == email:
                return user
        return None
    
    def create_user(self, user: UserInDB) -> UserInDB:
        """Create a new user"""
        self._users[user.username] = user
        return user
    
    def user_exists(self, username: str) -> bool:
        """Check if user exists"""
        return username in self._users


# Global user database instance
user_db = UserDatabase()