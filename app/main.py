from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, series, feedback, watchlist, episodes

app = FastAPI(title="MovieHub Backend (Supabase / ADP)")

# Adjust origins based on your frontend URLs
origins = [
    "http://localhost:5173",
    "http://localhost:5500",
    "https://<your-username>.github.io",
    "https://<your-username>.github.io/Netflix_Hub",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(series.router)
app.include_router(feedback.router)
app.include_router(watchlist.router)
app.include_router(episodes.router)


@app.get("/")
def root():
    return {"status": "ok", "message": "MovieHub backend is running"}