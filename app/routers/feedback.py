# app/routers/feedback.py

from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ADPFeedback, ADPAccount, ADPSeries, ADPUser
from app.schemas import FeedbackCreate, FeedbackItem, FeedbackListResponse
from app.deps import get_current_user

router = APIRouter(prefix="/series/{series_id}/feedback", tags=["feedback"])


def _get_account_for_user(db: Session, user_id: int) -> ADPAccount:
    """Get the account linked to a user."""
    account = db.query(ADPAccount).filter(ADPAccount.adp_user_user_id == user_id).first()
    if not account:
        raise HTTPException(status_code=400, detail="No account linked to this user")
    return account


@router.post("/", response_model=FeedbackItem)
def add_feedback(
    series_id: int,
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(get_current_user),
):
    """Add or update feedback for a series."""
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    account = _get_account_for_user(db, user.user_id)
    
    # Check if feedback already exists (upsert)
    fb = (
        db.query(ADPFeedback)
        .filter(
            ADPFeedback.adp_account_account_id == account.account_id,
            ADPFeedback.adp_series_series_id == series_id,
        )
        .with_for_update()  # FOR UPDATE locking
        .first()
    )
    
    if fb:
        # Update existing feedback
        fb.rating = payload.rating
        fb.feedback_text = payload.feedback_text
        fb.feedback_date = date.today()
    else:
        # Create new feedback
        fb = ADPFeedback(
            adp_account_account_id=account.account_id,
            adp_series_series_id=series_id,
            rating=payload.rating,
            feedback_text=payload.feedback_text,
            feedback_date=date.today(),
        )
        db.add(fb)
    
    db.commit()
    
    return FeedbackItem(
        account_id=account.account_id,
        account_name=f"{account.first_name} {account.last_name}",
        rating=fb.rating,
        feedback_text=fb.feedback_text,
        feedback_date=fb.feedback_date,
    )


@router.get("/", response_model=FeedbackListResponse)
def list_feedback(
    series_id: int,
    db: Session = Depends(get_db),
):
    """List all feedback for a series with summary stats."""
    # Get feedback with account info
    rows = (
        db.query(ADPFeedback, ADPAccount)
        .join(ADPAccount, ADPAccount.account_id == ADPFeedback.adp_account_account_id)
        .filter(ADPFeedback.adp_series_series_id == series_id)
        .order_by(ADPFeedback.feedback_date.desc())
        .all()
    )
    
    # Get stats from denormalized series columns
    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    
    items = []
    for fb, account in rows:
        items.append(
            FeedbackItem(
                account_id=fb.adp_account_account_id,
                account_name=f"{account.first_name} {account.last_name}",
                rating=fb.rating,
                feedback_text=fb.feedback_text,
                feedback_date=fb.feedback_date,
            )
        )
    
    return FeedbackListResponse(
        average_rating=float(series.average_rating) if series and series.average_rating else None,
        rating_count=series.rating_count if series else 0,
        items=items,
    )
