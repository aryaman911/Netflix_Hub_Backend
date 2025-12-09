# app/schemas.py

from typing import Optional, List

from pydantic import BaseModel, EmailStr
from pydantic import ConfigDict


# ---------------------------------------------------------------------------
# Base class so Pydantic v2 will work nicely with SQLAlchemy models
# ---------------------------------------------------------------------------

class ORMModel(BaseModel):
    """
    Base model configured to read data from SQLAlchemy objects via attributes.
    """
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# User / Auth schemas
# ---------------------------------------------------------------------------

class UserBase(ORMModel):
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


class TokenData(BaseModel):
    sub: Optional[str] = None  # email/username embedded in the JWT


# ---------------------------------------------------------------------------
# Series / Episode schemas
# ---------------------------------------------------------------------------

class Episode(ORMModel):
    id: int
    title: str
    episode_number: int
    season_number: Optional[int] = None
    overview: Optional[str] = None
    runtime: Optional[int] = None


class SeriesBase(ORMModel):
    title: str
    overview: Optional[str] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    vote_average: Optional[float] = None


class SeriesCreate(SeriesBase):
    """
    Payload for creating a new series.
    Add/adjust fields if your DB has more required columns.
    """
    pass


class SeriesUpdate(ORMModel):
    """
    Payload for partial updates of a series.
    All fields are optional.
    """
    title: Optional[str] = None
    overview: Optional[str] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    vote_average: Optional[float] = None


class SeriesListItem(SeriesBase):
    """
    Lightweight representation used for lists (/series, search results, etc.).
    """
    id: int


class SeriesDetail(SeriesBase):
    """
    Detailed representation used for single item view.
    """
    id: int
    episodes: List[Episode] = []


# ---------------------------------------------------------------------------
# Generic response helpers (if you need them later)
# ---------------------------------------------------------------------------

class MessageResponse(BaseModel):
    detail: str
