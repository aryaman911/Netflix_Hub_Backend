from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import ADPUser, ADPUserRole, ADPRole, ADPAccount
from app.schemas import UserCreate, User, Token
from app.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=User)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    # check email / username availability
    if db.query(ADPUser).filter(ADPUser.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if db.query(ADPUser).filter(ADPUser.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = ADPUser(
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.flush()  # get user_id

    # Ensure USER role exists
    user_role_code = "USER"
    role = db.query(ADPRole).filter(ADPRole.role_code == user_role_code).first()
    if not role:
        role = ADPRole(role_code=user_role_code, role_name="Standard user")
        db.add(role)
        db.flush()

    user_role = ADPUserRole(user_id=user.user_id, role_code=user_role_code)
    db.add(user_role)

    # Create an ADPAccount for this user (dummy address data)
    # NOTE: account_id must be generated; if your DB has identity, it will auto-generate.
    # If not, we use max+1 as a simple approach.
    max_account_id = db.query(func.max(ADPAccount.account_id)).scalar()
    next_account_id = (max_account_id or 0) + 1

    account = ADPAccount(
        account_id=next_account_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        address_line1="Unknown",
        city="Unknown",
        state_province="Unknown",
        postal_code="00000",
        opened_date=date.today(),
        monthly_service_fee=0,
        adp_country_country_code="US",  # assume US exists in adp_country
        adp_user_user_id=user.user_id,
    )
    db.add(account)

    db.commit()
    db.refresh(user)

    roles = [user_role_code]
    return User(
        user_id=user.user_id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        roles=roles,
    )


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    # OAuth2PasswordRequestForm has: username, password
    user = db.query(ADPUser).filter(ADPUser.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    # load roles
    roles = (
        db.query(ADPUserRole.role_code)
        .filter(ADPUserRole.user_id == user.user_id)
        .all()
    )
    role_codes = [r.role_code for r in roles]

    access_token = create_access_token(user_id=user.user_id, roles=role_codes)
    return Token(access_token=access_token)


@router.get("/me", response_model=User)
def get_me(db: Session = Depends(get_db), token: Token = Depends()):
    # This is a bit redundant; typically you'd use the get_current_user dep,
    # but your frontend might just want a quick “who am I”.
    from app.deps import get_current_user, get_current_user_roles

    user = get_current_user(db=db, token=token.access_token)  # type: ignore
    roles = get_current_user_roles(db=db, user=user)  # type: ignore

    return User(
        user_id=user.user_id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        roles=roles,
    )