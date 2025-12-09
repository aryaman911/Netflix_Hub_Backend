# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import (
    auth,
    series,
    episodes,
    feedback,
    watchlist,
    users,
    accounts,
    reference,
    schedules,
    production,
)


# -------------------------------------
# Database Initialization
# -------------------------------------
# Note: In production, use Alembic migrations instead
Base.metadata.create_all(bind=engine)


# -------------------------------------
# FastAPI App Config
# -------------------------------------
app = FastAPI(
    title="Netflix Hub API",
    version="2.0.0",
    description="Complete Backend API for Netflix Hub (Movie Streaming App)",
    docs_url="/docs",
    redoc_url="/redoc",
)


# -------------------------------------
# CORS Configuration
# -------------------------------------
origins = [
    "https://aryaman911.github.io",
    "https://aryaman911.github.io/Netflix_Hub",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------
# Health Check Endpoint
# -------------------------------------
@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok", "version": "2.0.0"}


# -------------------------------------
# Register Routers
# -------------------------------------

# Auth & Users
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])

# Content
app.include_router(series.router, prefix="/series", tags=["series"])
app.include_router(episodes.router, prefix="/episodes", tags=["episodes"])
app.include_router(feedback.router, tags=["feedback"])
app.include_router(watchlist.router, prefix="/me/watchlist", tags=["watchlist"])

# Reference Data
app.include_router(reference.router, prefix="/reference", tags=["reference"])

# Scheduling
app.include_router(schedules.router, prefix="/schedules", tags=["schedules"])

# Production Management
app.include_router(production.router, prefix="/production", tags=["production"])


# -------------------------------------
# Root Endpoint
# -------------------------------------
@app.get("/", tags=["system"])
def root():
    return {
        "message": "Netflix Hub API is running",
        "version": "2.0.0",
        "docs": "/docs",
    }
