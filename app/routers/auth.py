# app/routers/auth.py

from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import bcrypt
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ADPUser, ADPUserRole, ADPAccount
from app.schemas import UserCreate, UserResponse, Token, TokenWithUser
from app.deps import create_access_token, get_current_user, get_user_roles

router = APIRouter()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using bcrypt directly."""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt directly."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user with their account.
    Uses FOR UPDATE locking to prevent race conditions on ID generation.
    """
    # Check if email already exists
    if db.query(ADPUser).filter(ADPUser.email == user_in.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Check if username already exists
    if db.query(ADPUser).filter(ADPUser.username == user_in.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    
    try:
        # ========================================================================
        # FOR UPDATE LOCKING - Prevents race condition when generating user_id
        # ========================================================================
        max_user_id = db.query(func.max(ADPUser.user_id)).with_for_update().scalar()
        next_user_id = (max_user_id or 0) + 1
        
        # Create user
        user = ADPUser(
            user_id=next_user_id,
            email=user_in.email,
            username=user_in.username,
            password_hash=get_password_hash(user_in.password),
            is_active=True,
        )
        db.add(user)
        
        # Assign USER role
        user_role = ADPUserRole(user_id=next_user_id, role_code="USER")
        db.add(user_role)
        
        # ========================================================================
        # FOR UPDATE LOCKING - Prevents race condition when generating account_id
        # ========================================================================
        max_account_id = db.query(func.max(ADPAccount.account_id)).with_for_update().scalar()
        next_account_id = (max_account_id or 0) + 1
        
        # Create linked account
        account = ADPAccount(
            account_id=next_account_id,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            address_line1=user_in.address_line1,
            city=user_in.city,
            state_province=user_in.state_province,
            postal_code=user_in.postal_code,
            opened_date=date.today(),
            monthly_service_fee=Decimal("9.99"),
            adp_country_country_code=user_in.country_code,
            adp_user_user_id=next_user_id,
        )
        db.add(account)
        
        db.commit()
        db.refresh(user)
        
        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            roles=["USER"],
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )


@router.post("/login", response_model=TokenWithUser)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login with email or username and password.
    Returns JWT token with user info.
    """
    # Find user by email or username
    user = db.query(ADPUser).filter(
        (ADPUser.email == form_data.username) | (ADPUser.username == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    
    # Get user roles
    roles = get_user_roles(user, db)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.user_id)},
        expires_delta=timedelta(minutes=1440),  # 24 hours
    )
    
    # Update last login (ignore errors)
    try:
        user.last_login_at = func.now()
        db.commit()
    except Exception:
        db.rollback()
    
    return TokenWithUser(
        access_token=access_token,
        token_type="bearer",
        user_id=user.user_id,
        username=user.username,
        email=user.email,
        roles=roles,
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    user: ADPUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current authenticated user's information."""
    roles = get_user_roles(user, db)
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        roles=roles,
    )
