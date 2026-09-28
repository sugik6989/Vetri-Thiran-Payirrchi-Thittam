"""
Authentication routes for PocketSmart AI
Handles login, registration, logout, and session management
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Response, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm

from app.config import TEMPLATES_DIR, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.schemas import UserRegister, UserInDB, Token
from app.models.user import user_db
from app.utils.auth_utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    authenticate_user,
    get_current_user,
    get_current_active_user,
    get_token,
    blacklisted_tokens,
    active_sessions,
)

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ============== Page Routes ==============

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve the login page"""
    # Check if user is already logged in
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Serve the registration page"""
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/logout")
async def logout(request: Request):
    """Logout user and redirect to login"""
    token = await get_token(request)
    if token:
        blacklisted_tokens.add(token)
        
        # Remove from active sessions
        try:
            from jose import jwt
            from app.config import SECRET_KEY, ALGORITHM
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username and username in active_sessions:
                del active_sessions[username]
        except Exception:
            pass
    
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response


# ============== API Routes ==============

@router.post("/register", response_model=dict)
async def register_user(user_data: UserRegister):
    """Handle new user registration"""
    # Check if username exists
    if user_db.user_exists(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    if user_db.get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = UserInDB(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name or user_data.username,
        hashed_password=get_password_hash(user_data.password),
        created_at=datetime.utcnow()
    )
    
    user_db.create_user(new_user)
    
    return {
        "message": "User registered successfully",
        "username": new_user.username
    }


@router.post("/token", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """Login endpoint to get access token"""
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/login")
async def login_user(response: Response, user_data: dict):
    """Alternative login endpoint that accepts JSON"""
    username = user_data.get("username")
    password = user_data.get("password")
    
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password required"
        )
    
    user = authenticate_user(username, password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Login successful"
    }


@router.get("/session-info")
async def get_session_info(current_user: UserInDB = Depends(get_current_active_user)):
    """Get current session information"""
    session_data = active_sessions.get(current_user.username, {})
    
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "login_time": session_data.get("login_time"),
        "session_active": True
    }


@router.get("/session-data")
async def get_session_data(current_user: UserInDB = Depends(get_current_active_user)):
    """Get detailed session data for personalization"""
    if current_user.username in active_sessions:
        session = active_sessions[current_user.username]
        return {
            "user_data": session.get("user_data", {}),
            "last_activity": session.get("last_activity")
        }
    return {"user_data": {}, "last_activity": None}