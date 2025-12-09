# app/auth.py

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app import models
from app.database import get_db
from app.config import settings
from app.schemas import TokenData


# --------------------------------------------------------------------
# Password hashing
# --------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if password matches hash."""
    if not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plaintext password."""
    return pwd_context.hash(password)


# --------------------------------------------------------------------
# JWT helpers
# --------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> TokenData:
    """Decode a JWT and return TokenData. Raises ValueError if invalid."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise ValueError("Invalid token: missing subject")
        return TokenData(user_id=int(sub))
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}")


# --------------------------------------------------------------------
# User lookup
# --------------------------------------------------------------------

def get_user_by_identifier(db: Session, identifier: str) -> Optional[models.ADPUser]:
    """Fetch a user by email or username."""
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


def authenticate_user(db: Session, identifier: str, password: str) -> Optional[models.ADPUser]:
    """Return user if credentials are valid, otherwise None."""
    user = get_user_by_identifier(db, identifier)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_user_roles(db: Session, user_id: int) -> list[str]:
    """Get role codes for a user."""
    roles = (
        db.query(models.ADPUserRole, models.ADPRole)
        .join(models.ADPRole, models.ADPRole.role_code == models.ADPUserRole.role_code)
        .filter(models.ADPUserRole.user_id == user_id)
        .all()
    )
    return [r.ADPRole.role_code for r in roles]


# --------------------------------------------------------------------
# Dependencies
# --------------------------------------------------------------------

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.ADPUser:
    """Get the current authenticated user from JWT token."""
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
    if user is None or not user.is_active:
        raise credentials_exception
    return user
