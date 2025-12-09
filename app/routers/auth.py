# app/routers/auth.py
#
# UPDATED: Signup now creates both ADPUser AND linked ADPAccount

from datetime import datetime, date, timedelta
from typing import List
from uuid import uuid4
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from sqlalchemy import func

from app import models, schemas
from app.database import get_db
from app.auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_user_by_identifier,
    get_user_roles,
)
from app.config import settings

router = APIRouter()


# -------------------------------------------------------------------------
# SIGNUP - Creates User AND linked Account
# -------------------------------------------------------------------------

@router.post("/signup", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def signup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account with linked ADP account.
    
    This creates:
    1. ADPUser record (for authentication)
    2. ADPAccount record (for user profile/address info)
    3. ADPUserRole record (assigns USER role)
    
    Uses FOR UPDATE to safely generate IDs.
    """
    # Check if email exists
    if get_user_by_identifier(db, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    # Check if username exists
    if get_user_by_identifier(db, user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Validate country code exists
    country = db.query(models.ADPCountry).filter(
        models.ADPCountry.country_code == user_in.country_code
    ).first()
    if not country:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid country code: {user_in.country_code}",
        )

    try:
        # Generate next user_id with locking
        max_user_id = (
            db.query(func.max(models.ADPUser.user_id))
            .with_for_update(nowait=False)
            .scalar()
        )
        next_user_id = (max_user_id or 0) + 1

        # Create user
        user = models.ADPUser(
            user_id=next_user_id,
            username=user_in.username,
            email=user_in.email,
            password_hash=get_password_hash(user_in.password),
            is_active=True,
            created_at=datetime.utcnow(),
        )
        db.add(user)

        # Assign default USER role if it exists
        user_role = db.query(models.ADPRole).filter(models.ADPRole.role_code == "USER").first()
        if user_role:
            db.add(models.ADPUserRole(user_id=next_user_id, role_code="USER"))

        # Generate next account_id with locking
        max_account_id = (
            db.query(func.max(models.ADPAccount.account_id))
            .with_for_update(nowait=False)
            .scalar()
        )
        next_account_id = (max_account_id or 0) + 1

        # Create linked account
        account = models.ADPAccount(
            account_id=next_account_id,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            address_line1=user_in.address_line1,
            city=user_in.city,
            state_province=user_in.state_province,
            postal_code=user_in.postal_code,
            opened_date=date.today(),
            monthly_service_fee=Decimal("9.99"),  # Default subscription fee
            adp_country_country_code=user_in.country_code,
            adp_user_user_id=next_user_id,  # Link to user
        )
        db.add(account)

        db.commit()
        db.refresh(user)

        return schemas.UserRead(
            id=user.user_id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
        )

    except OperationalError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Database busy. Please try again.",
        )


# -------------------------------------------------------------------------
# LOGIN
# -------------------------------------------------------------------------

@router.post("/login", response_model=schemas.TokenWithUser)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login with email or username. Returns JWT access token.
    NOTE: OAuth2PasswordRequestForm expects form data (x-www-form-urlencoded).
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    
    # Get client info for audit
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    if not user:
        # Log failed attempt if user exists
        existing_user = get_user_by_identifier(db, form_data.username)
        if existing_user:
            audit = models.ADPLoginAudit(
                user_id=existing_user.user_id,
                login_time=datetime.utcnow(),
                success=False,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            db.add(audit)
            db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    user.last_login_at = datetime.utcnow()

    # Log successful login
    audit = models.ADPLoginAudit(
        user_id=user.user_id,
        login_time=datetime.utcnow(),
        success=True,
        client_ip=client_ip,
        user_agent=user_agent,
    )
    db.add(audit)
    db.commit()

    # Get user roles
    roles = get_user_roles(db, user.user_id)

    # Create token
    access_token = create_access_token({
        "sub": str(user.user_id),
        "roles": roles
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "roles": roles,
    }


# -------------------------------------------------------------------------
# PASSWORD RESET
# -------------------------------------------------------------------------

@router.post("/password-reset/request", response_model=schemas.PasswordResetResponse)
def request_password_reset(
    payload: schemas.PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """Request a password reset token. In production, this would send an email."""
    user = get_user_by_identifier(db, payload.email)
    
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If the email exists, a reset link has been sent."}

    # Create reset token
    token = models.ADPPasswordReset(
        token_id=uuid4(),
        user_id=user.user_id,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=settings.PASSWORD_RESET_EXPIRE_HOURS),
    )
    db.add(token)
    db.commit()

    # In production, send email with token here
    return {"message": "If the email exists, a reset link has been sent."}


@router.post("/password-reset/confirm", response_model=schemas.PasswordResetResponse)
def confirm_password_reset(
    payload: schemas.PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    """Confirm password reset with token and set new password."""
    reset = (
        db.query(models.ADPPasswordReset)
        .filter(models.ADPPasswordReset.token_id == payload.token)
        .first()
    )

    if not reset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    if reset.used_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset token has already been used",
        )

    if reset.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset token has expired",
        )

    # Update password
    user = db.query(models.ADPUser).filter(models.ADPUser.user_id == reset.user_id).first()
    user.password_hash = get_password_hash(payload.new_password)

    # Mark token as used
    reset.used_at = datetime.utcnow()

    db.commit()

    return {"message": "Password has been reset successfully."}


# -------------------------------------------------------------------------
# LOGIN AUDIT
# -------------------------------------------------------------------------

@router.get("/login-audit/{user_id}", response_model=List[schemas.LoginAuditItem])
def get_login_audit(
    user_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get login audit history for a user (admin only in production)."""
    audits = (
        db.query(models.ADPLoginAudit)
        .filter(models.ADPLoginAudit.user_id == user_id)
        .order_by(models.ADPLoginAudit.login_time.desc())
        .limit(limit)
        .all()
    )
    return audits
