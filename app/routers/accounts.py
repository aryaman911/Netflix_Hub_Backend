# app/routers/accounts.py

from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user, require_admin, get_current_account

router = APIRouter()


# -------------------------------------------------------------------------
# GET MY ACCOUNT
# -------------------------------------------------------------------------

@router.get("/me", response_model=schemas.AccountRead)
def get_my_account(account: models.ADPAccount = Depends(get_current_account)):
    """Get the current user's account."""
    return account


# -------------------------------------------------------------------------
# CREATE ACCOUNT
# -------------------------------------------------------------------------

@router.post("/", response_model=schemas.AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: schemas.AccountCreate,
    db: Session = Depends(get_db),
    user: models.ADPUser = Depends(get_current_user),
):
    """Create an account for the current user."""
    # Check if user already has an account
    existing = db.query(models.ADPAccount).filter(
        models.ADPAccount.adp_user_user_id == user.user_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an account",
        )

    # Generate account_id
    max_id = db.query(func.max(models.ADPAccount.account_id)).scalar()
    next_id = (max_id or 0) + 1

    account = models.ADPAccount(
        account_id=next_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        address_line1=payload.address_line1,
        city=payload.city,
        state_province=payload.state_province,
        postal_code=payload.postal_code,
        opened_date=payload.opened_date or date.today(),
        monthly_service_fee=payload.monthly_service_fee,
        adp_country_country_code=payload.adp_country_country_code,
        adp_user_user_id=user.user_id,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


# -------------------------------------------------------------------------
# UPDATE ACCOUNT
# -------------------------------------------------------------------------

@router.patch("/me", response_model=schemas.AccountRead)
def update_my_account(
    payload: schemas.AccountUpdate,
    db: Session = Depends(get_db),
    account: models.ADPAccount = Depends(get_current_account),
):
    """Update the current user's account."""
    if payload.first_name is not None:
        account.first_name = payload.first_name
    if payload.last_name is not None:
        account.last_name = payload.last_name
    if payload.address_line1 is not None:
        account.address_line1 = payload.address_line1
    if payload.city is not None:
        account.city = payload.city
    if payload.state_province is not None:
        account.state_province = payload.state_province
    if payload.postal_code is not None:
        account.postal_code = payload.postal_code
    if payload.monthly_service_fee is not None:
        account.monthly_service_fee = payload.monthly_service_fee

    db.commit()
    db.refresh(account)
    return account


# -------------------------------------------------------------------------
# ADMIN: LIST ALL ACCOUNTS
# -------------------------------------------------------------------------

@router.get("/", response_model=List[schemas.AccountRead])
def list_accounts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: models.ADPUser = Depends(require_admin),
):
    """List all accounts (admin only)."""
    accounts = db.query(models.ADPAccount).offset(skip).limit(limit).all()
    return accounts


@router.get("/{account_id}", response_model=schemas.AccountRead)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    admin: models.ADPUser = Depends(require_admin),
):
    """Get a specific account (admin only)."""
    account = db.query(models.ADPAccount).filter(
        models.ADPAccount.account_id == account_id
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account
