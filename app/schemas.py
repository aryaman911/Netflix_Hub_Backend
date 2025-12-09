# app/schemas.py

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    # Account fields
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    address_line1: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state_province: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country_code: str = Field(..., min_length=2, max_length=3)


class UserResponse(UserBase):
    user_id: int
    is_active: bool
    roles: List[str] = []

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenWithUser(Token):
    user_id: int
    username: str
    email: str
    roles: List[str]


class LoginRequest(BaseModel):
    username: str  # Can be email or username
    password: str


# ============================================================================
# SERIES SCHEMAS
# ============================================================================

class Episode(BaseModel):
    episode_id: int
    episode_number: int
    title: str
    synopsis: Optional[str] = None
    runtime_minutes: Optional[int] = None

    class Config:
        from_attributes = True


class SeriesListItem(BaseModel):
    series_id: int
    name: str
    poster_url: Optional[str] = None
    maturity_rating: Optional[str] = None
    origin_country: Optional[str] = None
    release_date: Optional[date] = None
    language_code: Optional[str] = None
    avg_rating: Optional[float] = None

    class Config:
        from_attributes = True


class SeriesDetail(BaseModel):
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

    class Config:
        from_attributes = True


class SeriesCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    maturity_rating: Optional[str] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None
    release_date: date
    origin_country: str = Field(..., min_length=1, max_length=100)
    language_code: str = Field(..., min_length=2, max_length=5)
    num_episodes: Optional[int] = 0
    genre_codes: List[str] = []
    dub_language_codes: List[str] = []
    sub_language_codes: List[str] = []


class SeriesUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    maturity_rating: Optional[str] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None
    release_date: Optional[date] = None
    origin_country: Optional[str] = None
    language_code: Optional[str] = None
    num_episodes: Optional[int] = None


# ============================================================================
# FEEDBACK SCHEMAS
# ============================================================================

class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = None


class FeedbackItem(BaseModel):
    account_id: int
    account_name: Optional[str] = None
    rating: int
    feedback_text: Optional[str] = None
    feedback_date: date

    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    average_rating: Optional[float] = None
    rating_count: int = 0
    items: List[FeedbackItem] = []


# ============================================================================
# WATCHLIST SCHEMAS
# ============================================================================

class WatchlistItem(BaseModel):
    series_id: int
    series_name: str
    poster_url: Optional[str] = None
    added_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# VIEW HISTORY SCHEMAS
# ============================================================================

class ViewHistoryCreate(BaseModel):
    watch_status: str = Field(..., pattern="^(STARTED|IN_PROGRESS|FINISHED)$")


# ============================================================================
# REFERENCE SCHEMAS
# ============================================================================

class LanguageItem(BaseModel):
    language_code: str
    language_name: str

    class Config:
        from_attributes = True


class GenreItem(BaseModel):
    type_code: str
    type_name: str

    class Config:
        from_attributes = True


class CountryItem(BaseModel):
    country_code: str
    country_name: str

    class Config:
        from_attributes = True
