from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, series, feedback, watchlist, reference

app = FastAPI(title="Netflix Hub API", version="1.0.0")

# CORS - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(series.router, prefix="/series", tags=["Series"])
app.include_router(feedback.router, prefix="/series", tags=["Feedback"])
app.include_router(watchlist.router, prefix="/me", tags=["Watchlist"])
app.include_router(reference.router, prefix="/reference", tags=["Reference"])


@app.get("/")
def root():
    return {"message": "Netflix Hub API", "status": "running"}


@app.get("/health")
def health():
    return {"status": "healthy"}
