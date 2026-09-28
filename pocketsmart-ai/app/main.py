"""
PocketSmart AI - Main Application Entry Point
FastAPI application with all routes and middleware configured
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

from app.config import (
    APP_NAME,
    STATIC_DIR,
    TEMPLATES_DIR,
    UPLOADS_DIR,
)
from app.utils.auth_utils import (
    get_current_user,
    get_current_active_user,
    active_sessions,
)
from app.models.user import user_db

# Import routers
from app.routes.auth import router as auth_router
from app.routes.home_planner import router as home_router
from app.routes.party_planner import router as party_router
from app.routes.jewelry_planner import router as jewelry_router
from app.routes.history import router as history_router


# ============== Background Tasks ==============

async def cleanup_expired_sessions():
    """Background task to clean up expired sessions"""
    while True:
        try:
            current_time = datetime.utcnow()
            expired_sessions = []
            
            for username, session in list(active_sessions.items()):
                # Check if session has been inactive for more than 30 minutes
                last_activity = getattr(session, 'last_activity', None)
                if last_activity:
                    inactive_seconds = (current_time - last_activity).total_seconds()
                    if inactive_seconds > 1800:  # 30 minutes
                        expired_sessions.append(username)
            
            for username in expired_sessions:
                if username in active_sessions:
                    print(f"Removing expired session for {username}")
                    del active_sessions[username]
            
        except Exception as e:
            print(f"Error in session cleanup: {e}")
        
        # Wait 5 minutes before next cleanup
        await asyncio.sleep(300)


# ============== Lifespan ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print(f"Starting {APP_NAME}...")
    print(f"Static files: {STATIC_DIR}")
    print(f"Templates: {TEMPLATES_DIR}")
    print(f"Uploads: {UPLOADS_DIR}")
    
    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_expired_sessions())
    
    yield
    
    # Shutdown
    print(f"Shutting down {APP_NAME}...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


# ============== Application Setup ==============

app = FastAPI(
    title=APP_NAME,
    description="AI-Powered Budget & Recommendation Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include routers
app.include_router(auth_router)
app.include_router(home_router)
app.include_router(party_router)
app.include_router(jewelry_router)
app.include_router(history_router)


# ============== Main Routes ==============

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main landing page"""
    user = await get_current_user(request)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "user": user}
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """User dashboard page"""
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": APP_NAME,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============== Main Entry Point ==============

if __name__ == "__main__":
    import uvicorn
    print(f"Starting {APP_NAME}...")
    print("Access the application at: http://localhost:8000")
    print("Demo credentials: username='demo', password='demo123'")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )