"""
Authentication utilities for JWT token management
"""

from datetime import datetime, timedelta
from typing import Optional, Set
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.schemas import TokenData, UserInDB
from app.models.user import user_db

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", auto_error=False)

# Token blacklist for logout
blacklisted_tokens: Set[str] = set()

# Active sessions
active_sessions: dict = {}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """Decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return TokenData(username=username)
    except JWTError:
        return None


async def get_token(request: Request) -> Optional[str]:
    """Extract token from request (cookie or header)"""
    # Try cookie first
    token = request.cookies.get("access_token")
    if token:
        return token
    
    # Try Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    
    return None


async def get_current_user(request: Request) -> Optional[UserInDB]:
    """Get current user from token"""
    token = await get_token(request)
    if not token:
        return None
    
    # Check if token is blacklisted
    if token in blacklisted_tokens:
        return None
    
    token_data = decode_token(token)
    if token_data is None or token_data.username is None:
        return None
    
    user = user_db.get_user(token_data.username)
    return user


async def get_current_active_user(request: Request) -> UserInDB:
    """Get current active user (raises exception if not authenticated)"""
    user = await get_current_user(request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user by username and password"""
    user = user_db.get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user