# app/routers/episodes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ADPViewHistory, ADPEpisode, ADPAccount, ADPUser
from app.schemas import ViewHistoryCreate
from app.deps import get_current_user

router = APIRouter()


def _get_account_for_user(db: Session, user_id: int) -> ADPAccount:
    """Get the account linked to a user."""
    account = db.query(ADPAccount).filter(ADPAccount.adp_user_user_id == user_id).first()
    if not account:
        raise HTTPException(status_code=400, detail="No account linked to this user")
    return account


@router.post("/{episode_id}/view", status_code=status.HTTP_204_NO_CONTENT)
def record_view(
    episode_id: int,
    payload: ViewHistoryCreate,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(get_current_user),
):
    """Record that a user viewed an episode."""
    episode = db.query(ADPEpisode).filter(ADPEpisode.episode_id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    account = _get_account_for_user(db, user.user_id)
    
    # Generate view_id with locking
    max_id = db.query(func.max(ADPViewHistory.view_id)).with_for_update().scalar()
    next_id = (max_id or 0) + 1
    
    vh = ADPViewHistory(
        view_id=next_id,
        adp_account_account_id=account.account_id,
        adp_episode_episode_id=episode_id,
        watch_status=payload.watch_status,
    )
    db.add(vh)
    db.commit()
