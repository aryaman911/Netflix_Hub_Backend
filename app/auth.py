# app/routers/auth.py
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import UserCreate, UserRead, Token
from app.config import settings

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def get_user_by_email_or_username(db: Session, identifier: str) -> models.User | None:
    return (
        db.query(models.User)
        .filter(
            (models.User.email == identifier)
            | (models.User.username == identifier)
        )
        .first()
    )


# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------

@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    # unique email/username check
    existing = (
        db.query(models.User)
        .filter(
            (models.User.email == user_in.email)
            | (models.User.username == user_in.username)
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered.",
        )

    db_user = models.User(
        username=user_in.username,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login with either email or username as `username` field + password.
    Frontend sends:
        { username: "<email or username>", password: "..." }
    """
    user = get_user_by_email_or_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.user_id)}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
