from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ADPUser, ADPUserRole, ADPAccount
from ..schemas import UserCreate, UserResponse, TokenWithUser
from ..deps import hash_password, verify_password, create_access_token, get_current_user, get_user_roles

router = APIRouter()


@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check email exists
    if db.query(ADPUser).filter(ADPUser.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check username exists
    if db.query(ADPUser).filter(ADPUser.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    try:
        # Get next user_id with FOR UPDATE lock
        max_user_id = db.query(func.max(ADPUser.user_id)).with_for_update().scalar()
        next_user_id = (max_user_id or 0) + 1
        
        # Create user
        user = ADPUser(
            user_id=next_user_id,
            email=user_in.email,
            username=user_in.username,
            password_hash=hash_password(user_in.password),
            is_active=True,
        )
        db.add(user)
        
        # Assign USER role
        user_role = ADPUserRole(user_id=next_user_id, role_code="USER")
        db.add(user_role)
        
        # Get next account_id with FOR UPDATE lock
        max_account_id = db.query(func.max(ADPAccount.account_id)).with_for_update().scalar()
        next_account_id = (max_account_id or 0) + 1
        
        # Create account
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
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@router.post("/login", response_model=TokenWithUser)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Find user by email or username
    user = db.query(ADPUser).filter(
        (ADPUser.email == form_data.username) | (ADPUser.username == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    roles = get_user_roles(user, db)
    access_token = create_access_token(data={"sub": str(user.user_id)})
    
    # Update last login
    try:
        user.last_login_at = func.now()
        db.commit()
    except:
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
def get_me(user: ADPUser = Depends(get_current_user), db: Session = Depends(get_db)):
    roles = get_user_roles(user, db)
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        roles=roles,
    )
