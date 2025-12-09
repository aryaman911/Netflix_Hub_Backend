# app/schemas.py

from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


# -------------------------
# User Schemas
# -------------------------

class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username_or_email: str
    password: str


class UserRead(UserBase):
    """
    Returned to the frontend after signup / login.
    """
    id: int
    role: str
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# Auth / Token Schemas
# -------------------------

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None


# -------------------------
# Series Schemas
# -------------------------

class SeriesBase(BaseModel):
    title: str
    description: Optional[str] = None
    genre: Optional[str] = None
    release_year: Optional[int] = None
    image_url: Optional[str] = None
    is_featured: bool = False


class SeriesCreate(SeriesBase):
    pass


class SeriesUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    release_year: Optional[int] = None
    image_url: Optional[str] = None
    is_featured: Optional[bool] = None


class SeriesRead(SeriesBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# Feedback Schemas
# -------------------------

class FeedbackCreate(BaseModel):
    message: str
    rating: Optional[int] = None  # 1-5 stars
    series_id: Optional[int] = None


class FeedbackRead(FeedbackCreate):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)
