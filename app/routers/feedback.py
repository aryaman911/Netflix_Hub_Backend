from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ADPUser, ADPAccount, ADPFeedback, ADPSeries
from ..schemas import FeedbackCreate, FeedbackListResponse, FeedbackResponse
from ..deps import get_current_user

router = APIRouter()


@router.get("/{series_id}/feedback", response_model=FeedbackListResponse)
def get_series_feedback(series_id: int, db: Session = Depends(get_db)):
    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    feedbacks = db.query(ADPFeedback).filter(
        ADPFeedback.adp_series_series_id == series_id
    ).all()
    
    items = []
    for fb in feedbacks:
        account = fb.account
        items.append(FeedbackResponse(
            rating=fb.rating,
            feedback_text=fb.feedback_text,
            feedback_date=fb.feedback_date,
            account_name=f"{account.first_name} {account.last_name[0]}." if account else "User",
        ))
    
    return FeedbackListResponse(
        average_rating=float(series.average_rating) if series.average_rating else None,
        rating_count=series.rating_count or 0,
        items=items,
    )


@router.post("/{series_id}/feedback", response_model=FeedbackResponse, status_code=201)
def add_feedback(
    series_id: int,
    feedback_in: FeedbackCreate,
    user: ADPUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate rating
    if feedback_in.rating < 1 or feedback_in.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    
    # Get user's account
    account = db.query(ADPAccount).filter(ADPAccount.adp_user_user_id == user.user_id).first()
    if not account:
        raise HTTPException(status_code=400, detail="No account found for user")
    
    # Check series exists
    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    try:
        # Check if feedback already exists (update it)
        existing = db.query(ADPFeedback).filter(
            ADPFeedback.adp_account_account_id == account.account_id,
            ADPFeedback.adp_series_series_id == series_id,
        ).with_for_update().first()
        
        if existing:
            existing.rating = feedback_in.rating
            existing.feedback_text = feedback_in.feedback_text
            existing.feedback_date = date.today()
            fb = existing
        else:
            fb = ADPFeedback(
                adp_account_account_id=account.account_id,
                adp_series_series_id=series_id,
                rating=feedback_in.rating,
                feedback_text=feedback_in.feedback_text,
                feedback_date=date.today(),
            )
            db.add(fb)
        
        db.commit()
        db.refresh(fb)
        
        return FeedbackResponse(
            rating=fb.rating,
            feedback_text=fb.feedback_text,
            feedback_date=fb.feedback_date,
            account_name=f"{account.first_name} {account.last_name[0]}.",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
