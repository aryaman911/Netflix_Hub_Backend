# app/routers/feedback.py

from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import ADPFeedback, ADPAccount, ADPSeries, ADPUser
from app.schemas import FeedbackCreate, FeedbackItem, FeedbackListResponse
from app.deps import get_current_account

router = APIRouter(prefix="/series/{series_id}/feedback", tags=["feedback"])


def _update_series_rating(db: Session, series_id: int):
    """
    Update the denormalized average_rating and rating_count on the series.
    Call this after adding/updating/deleting feedback.
    """
    result = (
        db.query(
            func.avg(ADPFeedback.rating).label("avg"),
            func.count(ADPFeedback.rating).label("count"),
        )
        .filter(ADPFeedback.adp_series_series_id == series_id)
        .first()
    )

    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if series:
        series.average_rating = result.avg or 0
        series.rating_count = result.count or 0


# -------------------------------------------------------------------------
# ADD/UPDATE FEEDBACK
# -------------------------------------------------------------------------

@router.post("/", response_model=FeedbackItem)
def add_feedback(
    series_id: int,
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    account: ADPAccount = Depends(get_current_account),
):
    """Add or update feedback for a series."""
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    # Check for existing feedback
    fb = (
        db.query(ADPFeedback)
        .filter(
            ADPFeedback.adp_account_account_id == account.account_id,
            ADPFeedback.adp_series_series_id == series_id,
        )
        .first()
    )

    if fb:
        # Update existing
        fb.rating = payload.rating
        fb.feedback_text = payload.feedback_text
        fb.feedback_date = date.today()
    else:
        # Create new
        fb = ADPFeedback(
            adp_account_account_id=account.account_id,
            adp_series_series_id=series_id,
            rating=payload.rating,
            feedback_text=payload.feedback_text,
            feedback_date=date.today(),
        )
        db.add(fb)

    # Update denormalized rating on series
    db.flush()  # Ensure feedback is saved before aggregating
    _update_series_rating(db, series_id)

    db.commit()

    return FeedbackItem(
        account_id=account.account_id,
        account_name=f"{account.first_name} {account.last_name}",
        rating=fb.rating,
        feedback_text=fb.feedback_text,
        feedback_date=fb.feedback_date,
    )


# -------------------------------------------------------------------------
# LIST FEEDBACK
# -------------------------------------------------------------------------

@router.get("/", response_model=FeedbackListResponse)
def list_feedback(
    series_id: int,
    db: Session = Depends(get_db),
):
    """List all feedback for a series."""
    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    rows = (
        db.query(ADPFeedback, ADPAccount)
        .join(ADPAccount, ADPAccount.account_id == ADPFeedback.adp_account_account_id)
        .filter(ADPFeedback.adp_series_series_id == series_id)
        .order_by(ADPFeedback.feedback_date.desc())
        .all()
    )

    items = [
        FeedbackItem(
            account_id=fb.adp_account_account_id,
            account_name=f"{account.first_name} {account.last_name}",
            rating=fb.rating,
            feedback_text=fb.feedback_text,
            feedback_date=fb.feedback_date,
        )
        for fb, account in rows
    ]

    return FeedbackListResponse(
        average_rating=float(series.average_rating) if series.average_rating else None,
        rating_count=series.rating_count,
        items=items,
    )


# -------------------------------------------------------------------------
# DELETE FEEDBACK
# -------------------------------------------------------------------------

@router.delete("/", status_code=204)
def delete_my_feedback(
    series_id: int,
    db: Session = Depends(get_db),
    account: ADPAccount = Depends(get_current_account),
):
    """Delete the current user's feedback for a series."""
    fb = (
        db.query(ADPFeedback)
        .filter(
            ADPFeedback.adp_account_account_id == account.account_id,
            ADPFeedback.adp_series_series_id == series_id,
        )
        .first()
    )

    if not fb:
        raise HTTPException(status_code=404, detail="No feedback found")

    db.delete(fb)
    
    # Update denormalized rating
    _update_series_rating(db, series_id)
    
    db.commit()
