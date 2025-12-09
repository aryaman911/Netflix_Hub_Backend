from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import ADPUser, ADPAccount, ADPWatchlist, ADPSeries
from ..schemas import WatchlistItem
from ..deps import get_current_user

router = APIRouter()


@router.get("/watchlist", response_model=List[WatchlistItem])
def get_watchlist(user: ADPUser = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.query(ADPAccount).filter(ADPAccount.adp_user_user_id == user.user_id).first()
    if not account:
        return []
    
    items = db.query(ADPWatchlist).filter(
        ADPWatchlist.adp_account_account_id == account.account_id
    ).all()
    
    return [
        WatchlistItem(
            series_id=item.series.series_id,
            series_name=item.series.name,
            poster_url=item.series.poster_url,
            added_at=item.added_at,
        )
        for item in items if item.series
    ]


@router.post("/watchlist/{series_id}", status_code=201)
def add_to_watchlist(
    series_id: int,
    user: ADPUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = db.query(ADPAccount).filter(ADPAccount.adp_user_user_id == user.user_id).first()
    if not account:
        raise HTTPException(status_code=400, detail="No account found")
    
    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    # Check if already in watchlist
    existing = db.query(ADPWatchlist).filter(
        ADPWatchlist.adp_account_account_id == account.account_id,
        ADPWatchlist.adp_series_series_id == series_id,
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already in watchlist")
    
    try:
        item = ADPWatchlist(
            adp_account_account_id=account.account_id,
            adp_series_series_id=series_id,
        )
        db.add(item)
        db.commit()
        return {"message": "Added to watchlist"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{series_id}", status_code=204)
def remove_from_watchlist(
    series_id: int,
    user: ADPUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = db.query(ADPAccount).filter(ADPAccount.adp_user_user_id == user.user_id).first()
    if not account:
        raise HTTPException(status_code=400, detail="No account found")
    
    item = db.query(ADPWatchlist).filter(
        ADPWatchlist.adp_account_account_id == account.account_id,
        ADPWatchlist.adp_series_series_id == series_id,
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Not in watchlist")
    
    try:
        db.delete(item)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
