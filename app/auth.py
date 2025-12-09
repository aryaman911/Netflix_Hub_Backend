# app/auth.py

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app import models
from app.database import get_db

# --------------------------------------------------------------------
# JWT / security configuration
# --------------------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# This must match the login route (POST /auth/login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class TokenData(BaseModel):
    sub: Optional[str] = None  # user id as string


# --------------------------------------------------------------------
# Password helpers
# --------------------------------------------------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if `plain_password` matches `hashed_password`."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plaintext password."""
    return pwd_context.hash(password)


# --------------------------------------------------------------------
# JWT helpers
# --------------------------------------------------------------------

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_access_token_for_user(user: models.User) -> str:
    """
    Convenience helper: create a token for a given user.
    Encodes the user_id as the `sub` (subject) claim.
    """
    return create_access_token({"sub": str(user.user_id)})


# --------------------------------------------------------------------
# User lookup / authentication
# --------------------------------------------------------------------

def get_user_by_identifier(
    db: Session, identifier: str
) -> Optional[models.User]:
    """
    Fetch a user either by email or username.
    `identifier` is whatever the user typed in the login form.
    """
    return (
        db.query(models.User)
        .filter(
            or_(
                models.User.email == identifier,
            #   models.User.username == identifier,  # enable if you have username column
            )
        )
        .first()
    )


def authenticate_user(
    db: Session, identifier: str, password: str
) -> Optional[models.User]:
    """
    Return user if credentials are valid, otherwise None.
    """
    user = get_user_by_identifier(db, identifier)
    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


# --------------------------------------------------------------------
# Dependencies for protected routes
# --------------------------------------------------------------------

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    Decode the JWT, fetch the user from DB and return it.
    Used as a dependency in routes that require authentication.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub: str | None = payload.get("sub")
        if sub is None:
            raise credentials_exception
        token_data = TokenData(sub=sub)
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).get(int(token_data.sub))
    if user is None:
        raise credentials_exception

    return user
