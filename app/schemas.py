from datetime import datetime, date, timedelta
from typing import List, Optional

from pydantic import BaseModel, EmailStr


# ---------------------------
# Auth / user schemas
# ---------------------------

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int
    roles: List[str]


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str
    first_name: str
    last_name: str


class User(BaseModel):
    user_id: int
    email: EmailStr
    username: str
    is_active: bool
    roles: List[str]

    class Config:
        from_attributes = True


# ---------------------------
# Series / episode schemas
# ---------------------------

class Episode(BaseModel):
    episode_id: int
    episode_number: int
    title: str
    runtime_minutes: Optional[int] = None
    synopsis: Optional[str] = None

    class Config:
        from_attributes = True


class SeriesBase(BaseModel):
    name: str
    description: Optional[str] = None
    maturity_rating: Optional[str] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None
    release_date: date
    origin_country: str
    language_code: str
    genre_codes: List[str] = []
    dub_language_codes: List[str] = []
    sub_language_codes: List[str] = []


class SeriesCreate(SeriesBase):
    num_episodes: int


class SeriesUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    maturity_rating: Optional[str] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None


class SeriesListItem(BaseModel):
    series_id: int
    name: str
    poster_url: Optional[str] = None
    maturity_rating: Optional[str] = None
    origin_country: str
    language_code: str
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
    release_date: date
    origin_country: str
    language_code: str
    genres: List[str]
    dub_languages: List[str]
    sub_languages: List[str]
    avg_rating: Optional[float]
    episodes: List[Episode]

    class Config:
        from_attributes = True


# ---------------------------
# Feedback
# ---------------------------

class FeedbackCreate(BaseModel):
    rating: int
    feedback_text: Optional[str] = None


class FeedbackItem(BaseModel):
    account_id: int
    rating: int
    feedback_text: Optional[str]
    feedback_date: date

    class Config:
        from_attributes = True


# ---------------------------
# Watchlist
# ---------------------------

class WatchlistItem(BaseModel):
    series_id: int
    series_name: str
    poster_url: Optional[str] = None
    added_at: datetime

    class Config:
        from_attributes = True


# ---------------------------
# View history
# ---------------------------

class ViewHistoryCreate(BaseModel):
    watch_status: str  # STARTED | IN_PROGRESS | FINISHED