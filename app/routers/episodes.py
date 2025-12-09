# app/routers/episodes.py

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import ADPEpisode, ADPSeries, ADPViewHistory, ADPUser, ADPAccount
from app.schemas import EpisodeRead, EpisodeCreate, EpisodeUpdate, ViewHistoryCreate
from app.deps import get_current_user, require_admin, get_current_account

router = APIRouter()


# -------------------------------------------------------------------------
# LIST EPISODES FOR A SERIES
# -------------------------------------------------------------------------

@router.get("/series/{series_id}", response_model=List[EpisodeRead])
def list_episodes_for_series(
    series_id: int,
    db: Session = Depends(get_db),
):
    """Get all episodes for a series."""
    episodes = (
        db.query(ADPEpisode)
        .filter(ADPEpisode.adp_series_series_id == series_id)
        .order_by(ADPEpisode.episode_number)
        .all()
    )
    return episodes


# -------------------------------------------------------------------------
# GET SINGLE EPISODE
# -------------------------------------------------------------------------

@router.get("/{episode_id}", response_model=EpisodeRead)
def get_episode(episode_id: int, db: Session = Depends(get_db)):
    """Get a single episode by ID."""
    episode = db.query(ADPEpisode).filter(ADPEpisode.episode_id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode


# -------------------------------------------------------------------------
# CREATE EPISODE (ADMIN)
# -------------------------------------------------------------------------

@router.post("/", response_model=EpisodeRead, status_code=201)
def create_episode(
    payload: EpisodeCreate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Create a new episode (admin only)."""
    # Check series exists
    series = db.query(ADPSeries).filter(ADPSeries.series_id == payload.adp_series_series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    # Generate episode_id
    max_id = db.query(func.max(ADPEpisode.episode_id)).scalar()
    next_id = (max_id or 0) + 1

    episode = ADPEpisode(
        episode_id=next_id,
        episode_number=payload.episode_number,
        title=payload.title,
        adp_series_series_id=payload.adp_series_series_id,
        total_viewers=payload.total_viewers,
        tech_interrupt_yn=payload.tech_interrupt_yn,
        synopsis=payload.synopsis,
        runtime_minutes=payload.runtime_minutes,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(episode)

    # Update series episode count
    series.num_episodes = (
        db.query(ADPEpisode)
        .filter(ADPEpisode.adp_series_series_id == series.series_id)
        .count() + 1
    )

    db.commit()
    db.refresh(episode)
    return episode


# -------------------------------------------------------------------------
# UPDATE EPISODE (ADMIN)
# -------------------------------------------------------------------------

@router.patch("/{episode_id}", response_model=EpisodeRead)
def update_episode(
    episode_id: int,
    payload: EpisodeUpdate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Update an episode (admin only)."""
    episode = db.query(ADPEpisode).filter(ADPEpisode.episode_id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    if payload.episode_number is not None:
        episode.episode_number = payload.episode_number
    if payload.title is not None:
        episode.title = payload.title
    if payload.synopsis is not None:
        episode.synopsis = payload.synopsis
    if payload.runtime_minutes is not None:
        episode.runtime_minutes = payload.runtime_minutes
    if payload.total_viewers is not None:
        episode.total_viewers = payload.total_viewers
    if payload.tech_interrupt_yn is not None:
        episode.tech_interrupt_yn = payload.tech_interrupt_yn

    episode.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(episode)
    return episode


# -------------------------------------------------------------------------
# DELETE EPISODE (ADMIN)
# -------------------------------------------------------------------------

@router.delete("/{episode_id}", status_code=204)
def delete_episode(
    episode_id: int,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Delete an episode (admin only)."""
    episode = db.query(ADPEpisode).filter(ADPEpisode.episode_id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    series_id = episode.adp_series_series_id
    db.delete(episode)

    # Update series episode count
    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if series:
        series.num_episodes = (
            db.query(ADPEpisode)
            .filter(ADPEpisode.adp_series_series_id == series_id)
            .count()
        )

    db.commit()


# -------------------------------------------------------------------------
# RECORD VIEW
# -------------------------------------------------------------------------

@router.post("/{episode_id}/view", status_code=204)
def record_view(
    episode_id: int,
    payload: ViewHistoryCreate,
    db: Session = Depends(get_db),
    account: ADPAccount = Depends(get_current_account),
):
    """Record that the user viewed an episode."""
    if payload.watch_status not in ("STARTED", "IN_PROGRESS", "FINISHED"):
        raise HTTPException(status_code=400, detail="Invalid watch status")

    episode = db.query(ADPEpisode).filter(ADPEpisode.episode_id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Generate view_id
    max_id = db.query(func.max(ADPViewHistory.view_id)).scalar()
    next_id = (max_id or 0) + 1

    vh = ADPViewHistory(
        view_id=next_id,
        adp_account_account_id=account.account_id,
        adp_episode_episode_id=episode_id,
        watch_status=payload.watch_status,
        started_at=datetime.utcnow(),
    )
    db.add(vh)

    # Update total viewers
    episode.total_viewers += 1

    db.commit()
