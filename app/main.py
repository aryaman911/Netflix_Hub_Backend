# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, series


# -------------------------------------
# Database Initialization
# -------------------------------------
Base.metadata.create_all(bind=engine)


# -------------------------------------
# FastAPI App Config
# -------------------------------------
app = FastAPI(
    title="Netflix Hub API",
    version="1.0.0",
    description="Backend API for Netflix Hub (Movie Streaming App)",
)


# -------------------------------------
# CORS Configuration
# -------------------------------------
origins = [
    "https://aryaman911.github.io",   # your GitHub Pages root
    "https://aryaman911.github.io/Netflix_Hub",  # repo pages
    "http://localhost:5500",          # local file-server testing
    "http://127.0.0.1:5500",
    "http://localhost:8000",
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
    return {"status": "ok"}


# -------------------------------------
# Register Routers
# -------------------------------------
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(series.router, prefix="/series", tags=["series"])


# -------------------------------------
# Root Endpoint
# -------------------------------------
@app.get("/", tags=["system"])
def root():
    return {"message": "Netflix Hub API is running"}
