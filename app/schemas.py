# app/schemas.py

from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, ConfigDict


# ---------------------------------------------------------------------------
# Base class so Pydantic v2 will work nicely with SQLAlchemy models
# ---------------------------------------------------------------------------

class ORMModel(BaseModel):
    """Base model configured to read data from SQLAlchemy objects via attributes."""
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# User / Auth schemas
# ---------------------------------------------------------------------------

class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int


class UserLogin(BaseModel):
    """
    Used for login requests. The frontend sends `identifier` which can be
    either email or username, plus `password`.
    """
    identifier: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenWithUser(Token):
    """Token response that includes user info for the frontend."""
    user_id: int
    roles: List[str] = []


class TokenData(BaseModel):
    sub: Optional[str] = None


# ---------------------------------------------------------------------------
# Episode schemas
# ---------------------------------------------------------------------------

class Episode(ORMModel):
    episode_id: int
    episode_number: int
    title: str
    synopsis: Optional[str] = None
    runtime_minutes: Optional[int] = None


# ---------------------------------------------------------------------------
# Series schemas - FIXED: aligned with actual model fields
# ---------------------------------------------------------------------------

class SeriesListItem(ORMModel):
    """Lightweight representation used for lists."""
    series_id: int
    name: str
    poster_url: Optional[str] = None
    maturity_rating: Optional[str] = None
    origin_country: Optional[str] = None
    release_date: Optional[date] = None
    language_code: Optional[str] = None
    avg_rating: Optional[float] = None


class SeriesDetail(ORMModel):
    """Detailed representation used for single item view."""
    series_id: int
    name: str
    description: Optional[str] = None
    maturity_rating: Optional[str] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None
    release_date: Optional[date] = None
    origin_country: Optional[str] = None
    num_episodes: Optional[int] = None
    language_code: Optional[str] = None
    genres: List[str] = []
    dub_languages: List[str] = []
    sub_languages: List[str] = []
    avg_rating: Optional[float] = None
    rating_count: int = 0
    episodes: List[Episode] = []


class SeriesCreate(BaseModel):
    """Payload for creating a new series."""
    name: str
    language_code: str
    origin_country: str
    release_date: date
    num_episodes: Optional[int] = 0
    description: Optional[str] = None
    maturity_rating: Optional[str] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None
    genre_codes: Optional[List[str]] = []
    dub_language_codes: Optional[List[str]] = []
    sub_language_codes: Optional[List[str]] = []


class SeriesUpdate(BaseModel):
    """Payload for partial updates of a series. All fields are optional."""
    name: Optional[str] = None
    description: Optional[str] = None
    maturity_rating: Optional[str] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None
    origin_country: Optional[str] = None
    language_code: Optional[str] = None
    num_episodes: Optional[int] = None
    release_date: Optional[date] = None


# ---------------------------------------------------------------------------
# Feedback schemas
# ---------------------------------------------------------------------------

class FeedbackCreate(BaseModel):
    rating: int  # 1-5
    feedback_text: Optional[str] = None


class FeedbackItem(ORMModel):
    account_id: int
    account_name: Optional[str] = None
    rating: int
    feedback_text: Optional[str] = None
    feedback_date: Optional[date] = None


class FeedbackListResponse(BaseModel):
    """Response for listing feedback with summary stats."""
    average_rating: Optional[float] = None
    rating_count: int = 0
    items: List[FeedbackItem] = []


# ---------------------------------------------------------------------------
# Watchlist schemas
# ---------------------------------------------------------------------------

class WatchlistItem(ORMModel):
    series_id: int
    series_name: str
    poster_url: Optional[str] = None
    added_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# View History schemas
# ---------------------------------------------------------------------------

class ViewHistoryCreate(BaseModel):
    watch_status: str  # "STARTED", "IN_PROGRESS", "FINISHED"


# ---------------------------------------------------------------------------
# Generic response helpers
# ---------------------------------------------------------------------------

class MessageResponse(BaseModel):
    detail: str
