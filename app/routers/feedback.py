from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ADPFeedback, ADPAccount, ADPSeries
from app.schemas import FeedbackCreate, FeedbackItem
from app.deps import get_current_user
from app.models import ADPUser

router = APIRouter(prefix="/series/{series_id}/feedback", tags=["feedback"])


def _get_account_for_user(db: Session, user_id: int) -> ADPAccount:
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
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    account = _get_account_for_user(db, user.user_id)

    fb = (
        db.query(ADPFeedback)
        .filter(
            ADPFeedback.adp_account_account_id == account.account_id,
            ADPFeedback.adp_series_series_id == series_id,
        )
        .first()
    )

    if fb:
        fb.rating = payload.rating
        fb.feedback_text = payload.feedback_text
        fb.feedback_date = date.today()
    else:
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
        rating=fb.rating,
        feedback_text=fb.feedback_text,
        feedback_date=fb.feedback_date,
    )


@router.get("/", response_model=List[FeedbackItem])
def list_feedback(
    series_id: int,
    db: Session = Depends(get_db),
):
    rows = (
        db.query(ADPFeedback)
        .filter(ADPFeedback.adp_series_series_id == series_id)
        .all()
    )

    return [
        FeedbackItem(
            account_id=row.adp_account_account_id,
            rating=row.rating,
            feedback_text=row.feedback_text,
            feedback_date=row.feedback_date,
        )
        for row in rows
    ]