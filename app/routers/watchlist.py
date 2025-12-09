# app/routers/watchlist.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ADPWatchlist, ADPAccount, ADPSeries
from app.schemas import WatchlistItem
from app.deps import get_current_account

router = APIRouter()


# -------------------------------------------------------------------------
# GET WATCHLIST
# -------------------------------------------------------------------------

@router.get("/", response_model=List[WatchlistItem])
def get_watchlist(
    db: Session = Depends(get_db),
    account: ADPAccount = Depends(get_current_account),
):
    """Get the current user's watchlist."""
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


# -------------------------------------------------------------------------
# ADD TO WATCHLIST
# -------------------------------------------------------------------------

@router.post("/{series_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_to_watchlist(
    series_id: int,
    db: Session = Depends(get_db),
    account: ADPAccount = Depends(get_current_account),
):
    """Add a series to the watchlist."""
    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    # Check if already on watchlist
    existing = (
        db.query(ADPWatchlist)
        .filter(
            ADPWatchlist.adp_account_account_id == account.account_id,
            ADPWatchlist.adp_series_series_id == series_id,
        )
        .first()
    )
    if existing:
        return  # Already on watchlist

    wl = ADPWatchlist(
        adp_account_account_id=account.account_id,
        adp_series_series_id=series_id,
    )
    db.add(wl)
    db.commit()


# -------------------------------------------------------------------------
# REMOVE FROM WATCHLIST
# -------------------------------------------------------------------------

@router.delete("/{series_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    series_id: int,
    db: Session = Depends(get_db),
    account: ADPAccount = Depends(get_current_account),
):
    """Remove a series from the watchlist."""
    wl = (
        db.query(ADPWatchlist)
        .filter(
            ADPWatchlist.adp_account_account_id == account.account_id,
            ADPWatchlist.adp_series_series_id == series_id,
        )
        .first()
    )

    if not wl:
        raise HTTPException(status_code=404, detail="Not on watchlist")

    db.delete(wl)
    db.commit()


# -------------------------------------------------------------------------
# CHECK IF ON WATCHLIST
# -------------------------------------------------------------------------

@router.get("/{series_id}/check")
def check_watchlist(
    series_id: int,
    db: Session = Depends(get_db),
    account: ADPAccount = Depends(get_current_account),
):
    """Check if a series is on the user's watchlist."""
    exists = (
        db.query(ADPWatchlist)
        .filter(
            ADPWatchlist.adp_account_account_id == account.account_id,
            ADPWatchlist.adp_series_series_id == series_id,
        )
        .first()
    ) is not None

    return {"on_watchlist": exists}
