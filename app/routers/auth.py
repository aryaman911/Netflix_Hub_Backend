# app/routers/auth.py

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import (
    OAuth2PasswordRequestForm,
    OAuth2PasswordBearer,
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# --------- helper functions --------- #

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user_by_email_or_username(
    db: Session, identifier: str
) -> Optional[models.ADPUser]:
    """
    Look up a user by either email or username.
    """
    return (
        db.query(models.ADPUser)
        .filter(
            (models.ADPUser.email == identifier)
            | (models.ADPUser.username == identifier)
        )
        .first()
    )


def authenticate_user(
    db: Session, identifier: str, password: str
) -> Optional[models.ADPUser]:
    user = get_user_by_email_or_username(db, identifier)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


# --------- routes --------- #

@router.post(
    "/signup",
    response_model=schemas.UserRead,
    status_code=status.HTTP_201_CREATED,
)
def signup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new ADPUser account.
    Username OR email must be unique.
    """
    # Check existing by email or username
    if get_user_by_email_or_username(db, user_in.email) or get_user_by_email_or_username(
        db, user_in.username
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    user = models.ADPUser(
        username=user_in.username,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Map ADPUser -> UserRead
    return schemas.UserRead(
        id=user.user_id,
        username=user.username,
        email=user.email,
        role="user",      # default role for now
        is_active=True,   # ADPUser has no flag, so assume active
    )


@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login with either email or username (form_data.username)
    and password. Returns a JWT access token.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token({"sub": user.username})
    # schemas.Token has access_token + token_type; extra fields are ignored
    return {"access_token": access_token, "token_type": "bearer"}


# Dependency to get the current user from the token, usable in other routers
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.ADPUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_email_or_username(db, username)
    if user is None:
        raise credentials_exception
    return user
