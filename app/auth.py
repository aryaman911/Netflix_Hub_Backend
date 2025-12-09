# app/auth.py

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
from app.config import settings  # FIXED: use settings from config.py

# --------------------------------------------------------------------
# JWT / security configuration - FIXED: use settings object
# --------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# This must match the login route (POST /auth/login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class TokenData(BaseModel):
    user_id: int  # FIXED: store user_id directly


# --------------------------------------------------------------------
# Password helpers
# --------------------------------------------------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if `plain_password` matches `hashed_password`."""
    if not hashed_password:
        return False
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
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_access_token_for_user(user: models.ADPUser, roles: list[str] = None) -> str:
    """
    Convenience helper: create a token for a given user.
    Encodes the user_id and roles in the token.
    """
    return create_access_token({
        "sub": str(user.user_id),
        "roles": roles or []
    })


def decode_token(token: str) -> TokenData:
    """
    Decode a JWT and return TokenData.
    Raises ValueError if token is invalid.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise ValueError("Invalid token: missing subject")
        return TokenData(user_id=int(sub))
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}")


# --------------------------------------------------------------------
# User lookup / authentication
# --------------------------------------------------------------------

def get_user_by_identifier(
    db: Session,
    identifier: str,
) -> Optional[models.ADPUser]:
    """
    Fetch a user either by email or username.
    `identifier` is whatever the user typed in the login form.
    """
    return (
        db.query(models.ADPUser)
        .filter(
            or_(
                models.ADPUser.email == identifier,
                models.ADPUser.username == identifier,
            )
        )
        .first()
    )


def authenticate_user(
    db: Session,
    identifier: str,
    password: str,
) -> Optional[models.ADPUser]:
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
) -> models.ADPUser:
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
        token_data = decode_token(token)
    except ValueError:
        raise credentials_exception

    user = db.query(models.ADPUser).filter(models.ADPUser.user_id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    return user
