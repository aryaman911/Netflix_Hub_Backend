# app/routers/auth.py

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_user_by_identifier,
)
from app.models import ADPUserRole, ADPRole

# FIXED: Removed prefix="/auth" - it's now set in main.py only
router = APIRouter()


def get_user_roles(db: Session, user_id: int) -> List[str]:
    """Get role codes for a user."""
    roles = (
        db.query(ADPUserRole, ADPRole)
        .join(ADPRole, ADPRole.role_code == ADPUserRole.role_code)
        .filter(ADPUserRole.user_id == user_id)
        .all()
    )
    return [r.ADPRole.role_code for r in roles]


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
    if get_user_by_identifier(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    if get_user_by_identifier(db, user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Generate next user_id
    from sqlalchemy import func
    max_id = db.query(func.max(models.ADPUser.user_id)).scalar()
    next_id = (max_id or 0) + 1

    user = models.ADPUser(
        user_id=next_id,
        username=user_in.username,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return schemas.UserRead(
        id=user.user_id,
        username=user.username,
        email=user.email,
    )


@router.post("/login", response_model=schemas.TokenWithUser)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login with either email or username (form_data.username)
    and password. Returns a JWT access token plus user info.
    
    NOTE: OAuth2PasswordRequestForm expects form data (x-www-form-urlencoded),
    not JSON. The frontend must send data as FormData or URLSearchParams.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Get user roles
    roles = get_user_roles(db, user.user_id)

    # Create token with user_id and roles embedded
    access_token = create_access_token({
        "sub": str(user.user_id),
        "roles": roles
    })

    # FIXED: Return user_id and roles so frontend can store them
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "roles": roles,
    }
