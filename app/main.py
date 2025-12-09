# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, series, episodes, feedback, watchlist, reference

# ============================================================================
# APP CONFIGURATION
# ============================================================================

app = FastAPI(
    title="Netflix Hub API",
    version="2.0.0",
    description="Backend API for Netflix Hub (Movie Streaming Platform)",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================================
# CORS CONFIGURATION - ALLOW ALL ORIGINS FOR DEMO
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health", tags=["system"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "2.0.0"}


@app.get("/", tags=["system"])
def root():
    """Root endpoint."""
    return {
        "message": "Netflix Hub API is running",
        "version": "2.0.0",
        "docs": "/docs",
    }

# ============================================================================
# REGISTER ROUTERS
# ============================================================================

# Auth
app.include_router(auth.router, prefix="/auth", tags=["auth"])

# Content
app.include_router(series.router, prefix="/series", tags=["series"])
app.include_router(episodes.router, prefix="/episodes", tags=["episodes"])
app.include_router(feedback.router, tags=["feedback"])

# User Activity
app.include_router(watchlist.router, prefix="/me/watchlist", tags=["watchlist"])

# Reference Data
app.include_router(reference.router, prefix="/reference", tags=["reference"])
