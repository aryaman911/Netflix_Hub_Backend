# app/routers/watchlist.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ADPWatchlist, ADPAccount, ADPSeries, ADPUser
from app.schemas import WatchlistItem
from app.deps import get_current_user

router = APIRouter()


def _get_account_for_user(db: Session, user_id: int) -> ADPAccount:
    """Get the account linked to a user."""
    account = db.query(ADPAccount).filter(ADPAccount.adp_user_user_id == user_id).first()
    if not account:
        raise HTTPException(status_code=400, detail="No account linked to this user")
    return account


@router.get("/", response_model=List[WatchlistItem])
def get_watchlist(
    db: Session = Depends(get_db),
    user: ADPUser = Depends(get_current_user),
):
    """Get the current user's watchlist."""
    account = _get_account_for_user(db, user.user_id)
    
    rows = (
        db.query(ADPWatchlist, ADPSeries)
        .join(ADPSeries, ADPSeries.series_id == ADPWatchlist.adp_series_series_id)
        .filter(ADPWatchlist.adp_account_account_id == account.account_id)
        .order_by(ADPWatchlist.added_at.desc())
        .all()
    )
    
    return [
        WatchlistItem(
            series_id=series.series_id,
            series_name=series.name,
            poster_url=series.poster_url,
            added_at=wl.added_at,
        )
        for wl, series in rows
    ]


@router.post("/{series_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_to_watchlist(
    series_id: int,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(get_current_user),
):
    """Add a series to the user's watchlist."""
    account = _get_account_for_user(db, user.user_id)
    
    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    # Check if already in watchlist
    existing = (
        db.query(ADPWatchlist)
        .filter(
            ADPWatchlist.adp_account_account_id == account.account_id,
            ADPWatchlist.adp_series_series_id == series_id,
        )
        .first()
    )
    
    if existing:
        return  # Already in watchlist, silently succeed
    
    wl = ADPWatchlist(
        adp_account_account_id=account.account_id,
        adp_series_series_id=series_id,
    )
    db.add(wl)
    db.commit()


@router.delete("/{series_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    series_id: int,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(get_current_user),
):
    """Remove a series from the user's watchlist."""
    account = _get_account_for_user(db, user.user_id)
    
    existing = (
        db.query(ADPWatchlist)
        .filter(
            ADPWatchlist.adp_account_account_id == account.account_id,
            ADPWatchlist.adp_series_series_id == series_id,
        )
        .first()
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="Not in watchlist")
    
    db.delete(existing)
    db.commit()
