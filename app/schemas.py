from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime


# Auth Schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: str
    last_name: str
    address_line1: str
    city: str
    state_province: str
    postal_code: str
    country_code: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    user_id: int
    email: str
    username: str
    is_active: bool
    roles: List[str]

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenWithUser(Token):
    user_id: int
    username: str
    email: str
    roles: List[str]


# Series Schemas
class SeriesCreate(BaseModel):
    name: str
    release_date: date
    language_code: str
    origin_country: str
    num_episodes: int = 0
    description: Optional[str] = None
    maturity_rating: Optional[str] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None
    genre_codes: List[str] = []


class SeriesUpdate(BaseModel):
    name: Optional[str] = None
    release_date: Optional[date] = None
    language_code: Optional[str] = None
    origin_country: Optional[str] = None
    num_episodes: Optional[int] = None
    description: Optional[str] = None
    maturity_rating: Optional[str] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None
    genre_codes: Optional[List[str]] = None


class EpisodeResponse(BaseModel):
    episode_id: int
    episode_number: int
    title: str
    synopsis: Optional[str]
    runtime_minutes: Optional[int]

    class Config:
        from_attributes = True


class SeriesResponse(BaseModel):
    series_id: int
    name: str
    num_episodes: int
    release_date: date
    language_code: str
    origin_country: str
    description: Optional[str]
    maturity_rating: Optional[str]
    poster_url: Optional[str]
    banner_url: Optional[str]
    avg_rating: Optional[float]
    rating_count: int
    genres: List[str]
    dub_languages: List[str] = []
    sub_languages: List[str] = []
    episodes: List[EpisodeResponse] = []

    class Config:
        from_attributes = True


# Feedback Schemas
class FeedbackCreate(BaseModel):
    rating: int
    feedback_text: Optional[str] = None


class FeedbackResponse(BaseModel):
    rating: int
    feedback_text: Optional[str]
    feedback_date: date
    account_name: str

    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    average_rating: Optional[float]
    rating_count: int
    items: List[FeedbackResponse]


# Watchlist Schemas
class WatchlistItem(BaseModel):
    series_id: int
    series_name: str
    poster_url: Optional[str]
    added_at: datetime

    class Config:
        from_attributes = True


# Reference Schemas
class LanguageResponse(BaseModel):
    language_code: str
    language_name: str

    class Config:
        from_attributes = True


class GenreResponse(BaseModel):
    type_code: str
    type_name: str

    class Config:
        from_attributes = True


class CountryResponse(BaseModel):
    country_code: str
    country_name: str

    class Config:
        from_attributes = True
