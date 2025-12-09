# app/routers/schedules.py

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import ADPSchedule, ADPEpisode, ADPSeries, ADPUser
from app.schemas import ScheduleRead, ScheduleCreate, ScheduleUpdate
from app.deps import require_admin

router = APIRouter()


# -------------------------------------------------------------------------
# LIST SCHEDULES
# -------------------------------------------------------------------------

@router.get("/", response_model=List[ScheduleRead])
def list_schedules(
    start_after: Optional[datetime] = Query(None),
    start_before: Optional[datetime] = Query(None),
    series_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List schedules with optional filters."""
    q = (
        db.query(ADPSchedule, ADPEpisode, ADPSeries)
        .join(ADPEpisode, ADPEpisode.episode_id == ADPSchedule.adp_episode_episode_id)
        .join(ADPSeries, ADPSeries.series_id == ADPEpisode.adp_series_series_id)
    )

    if start_after:
        q = q.filter(ADPSchedule.start_datetime >= start_after)
    if start_before:
        q = q.filter(ADPSchedule.start_datetime <= start_before)
    if series_id:
        q = q.filter(ADPEpisode.adp_series_series_id == series_id)

    q = q.order_by(ADPSchedule.start_datetime).offset(skip).limit(limit)
    rows = q.all()

    return [
        ScheduleRead(
            schedule_id=schedule.schedule_id,
            start_datetime=schedule.start_datetime,
            end_datetime=schedule.end_datetime,
            adp_episode_episode_id=schedule.adp_episode_episode_id,
            episode_title=episode.title,
            series_name=series.name,
        )
        for schedule, episode, series in rows
    ]


# -------------------------------------------------------------------------
# GET SCHEDULE
# -------------------------------------------------------------------------

@router.get("/{schedule_id}", response_model=ScheduleRead)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Get a specific schedule."""
    row = (
        db.query(ADPSchedule, ADPEpisode, ADPSeries)
        .join(ADPEpisode, ADPEpisode.episode_id == ADPSchedule.adp_episode_episode_id)
        .join(ADPSeries, ADPSeries.series_id == ADPEpisode.adp_series_series_id)
        .filter(ADPSchedule.schedule_id == schedule_id)
        .first()
    )

    if not row:
        raise HTTPException(status_code=404, detail="Schedule not found")

    schedule, episode, series = row
    return ScheduleRead(
        schedule_id=schedule.schedule_id,
        start_datetime=schedule.start_datetime,
        end_datetime=schedule.end_datetime,
        adp_episode_episode_id=schedule.adp_episode_episode_id,
        episode_title=episode.title,
        series_name=series.name,
    )


# -------------------------------------------------------------------------
# CREATE SCHEDULE (ADMIN)
# -------------------------------------------------------------------------

@router.post("/", response_model=ScheduleRead, status_code=201)
def create_schedule(
    payload: ScheduleCreate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Create a new schedule (admin only)."""
    # Check episode exists
    episode = db.query(ADPEpisode).filter(ADPEpisode.episode_id == payload.adp_episode_episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Validate times
    if payload.end_datetime <= payload.start_datetime:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    # Generate schedule_id
    max_id = db.query(func.max(ADPSchedule.schedule_id)).scalar()
    next_id = (max_id or 0) + 1

    schedule = ADPSchedule(
        schedule_id=next_id,
        start_datetime=payload.start_datetime,
        end_datetime=payload.end_datetime,
        adp_episode_episode_id=payload.adp_episode_episode_id,
    )
    db.add(schedule)
    db.commit()

    return get_schedule(next_id, db)


# -------------------------------------------------------------------------
# UPDATE SCHEDULE (ADMIN)
# -------------------------------------------------------------------------

@router.patch("/{schedule_id}", response_model=ScheduleRead)
def update_schedule(
    schedule_id: int,
    payload: ScheduleUpdate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Update a schedule (admin only)."""
    schedule = db.query(ADPSchedule).filter(ADPSchedule.schedule_id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if payload.start_datetime is not None:
        schedule.start_datetime = payload.start_datetime
    if payload.end_datetime is not None:
        schedule.end_datetime = payload.end_datetime

    # Validate times
    if schedule.end_datetime <= schedule.start_datetime:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    db.commit()
    return get_schedule(schedule_id, db)


# -------------------------------------------------------------------------
# DELETE SCHEDULE (ADMIN)
# -------------------------------------------------------------------------

@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Delete a schedule (admin only)."""
    schedule = db.query(ADPSchedule).filter(ADPSchedule.schedule_id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    db.delete(schedule)
    db.commit()
