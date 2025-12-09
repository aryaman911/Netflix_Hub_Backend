# app/routers/series.py

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import (
    ADPSeries,
    ADPSeriesGenre,
    ADPSeriesType,
    ADPLanguage,
    ADPEpisode,
    ADPSeriesDub,
    ADPSeriesSub,
    ADPFeedback,
    ADPUser,
)
from app.schemas import SeriesListItem, SeriesDetail, SeriesCreate, SeriesUpdate, EpisodeRead
from app.deps import require_admin

router = APIRouter()


# -------------------------------------------------------------------------
# LIST SERIES
# -------------------------------------------------------------------------

@router.get("/", response_model=List[SeriesListItem])
def list_series(
    search: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List all series with optional filters."""
    q = db.query(ADPSeries)

    if search:
        q = q.filter(func.lower(ADPSeries.name).contains(search.lower()))

    if language:
        q = q.filter(ADPSeries.adp_language_language_code == language)

    if genre:
        q = q.join(ADPSeriesGenre).filter(ADPSeriesGenre.adp_series_type_type_code == genre)

    series_list = q.offset(skip).limit(limit).all()

    return [
        SeriesListItem(
            series_id=s.series_id,
            name=s.name,
            poster_url=s.poster_url,
            maturity_rating=s.maturity_rating,
            origin_country=s.origin_country,
            release_date=s.release_date,
            language_code=s.adp_language_language_code,
            average_rating=float(s.average_rating) if s.average_rating else None,
            rating_count=s.rating_count,
        )
        for s in series_list
    ]


# -------------------------------------------------------------------------
# GET SERIES DETAIL
# -------------------------------------------------------------------------

@router.get("/{series_id}", response_model=SeriesDetail)
def get_series_detail(series_id: int, db: Session = Depends(get_db)):
    """Get detailed info for a single series."""
    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    # Get genres
    genres = [g.adp_series_type_type_code for g in series.genres]

    # Get dub languages
    dub_langs = [d.adp_language_language_code for d in series.dubs]

    # Get sub languages
    sub_langs = [s.adp_language_language_code for s in series.subs]

    # Get episodes
    episodes = (
        db.query(ADPEpisode)
        .filter(ADPEpisode.adp_series_series_id == series_id)
        .order_by(ADPEpisode.episode_number)
        .all()
    )

    return SeriesDetail(
        series_id=series.series_id,
        name=series.name,
        num_episodes=series.num_episodes,
        release_date=series.release_date,
        language_code=series.adp_language_language_code,
        origin_country=series.origin_country,
        description=series.description,
        maturity_rating=series.maturity_rating,
        poster_url=series.poster_url,
        banner_url=series.banner_url,
        average_rating=float(series.average_rating) if series.average_rating else None,
        rating_count=series.rating_count,
        genres=genres,
        dub_languages=dub_langs,
        sub_languages=sub_langs,
        episodes=[
            EpisodeRead(
                episode_id=ep.episode_id,
                episode_number=ep.episode_number,
                title=ep.title,
                synopsis=ep.synopsis,
                runtime_minutes=ep.runtime_minutes,
                adp_series_series_id=ep.adp_series_series_id,
                total_viewers=ep.total_viewers,
                tech_interrupt_yn=ep.tech_interrupt_yn,
            )
            for ep in episodes
        ],
    )


# -------------------------------------------------------------------------
# CREATE SERIES (ADMIN)
# -------------------------------------------------------------------------

@router.post("/", response_model=SeriesDetail, status_code=201)
def create_series(
    payload: SeriesCreate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Create a new series (admin only)."""
    # Generate series_id
    max_id = db.query(func.max(ADPSeries.series_id)).scalar()
    next_id = (max_id or 0) + 1

    series = ADPSeries(
        series_id=next_id,
        name=payload.name,
        num_episodes=payload.num_episodes,
        release_date=payload.release_date,
        adp_language_language_code=payload.adp_language_language_code,
        origin_country=payload.origin_country,
        description=payload.description,
        maturity_rating=payload.maturity_rating,
        poster_url=payload.poster_url,
        banner_url=payload.banner_url,
        average_rating=0,
        rating_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(series)

    # Add genres
    for g in payload.genre_codes or []:
        db.add(ADPSeriesGenre(adp_series_series_id=next_id, adp_series_type_type_code=g))

    # Add dubs
    for lang in payload.dub_language_codes or []:
        db.add(ADPSeriesDub(adp_series_series_id=next_id, adp_language_language_code=lang))

    # Add subs
    for lang in payload.sub_language_codes or []:
        db.add(ADPSeriesSub(adp_series_series_id=next_id, adp_language_language_code=lang))

    db.commit()
    db.refresh(series)

    return get_series_detail(series.series_id, db)


# -------------------------------------------------------------------------
# UPDATE SERIES (ADMIN)
# -------------------------------------------------------------------------

@router.put("/{series_id}", response_model=SeriesDetail)
@router.patch("/{series_id}", response_model=SeriesDetail)
def update_series(
    series_id: int,
    payload: SeriesUpdate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Update a series (admin only)."""
    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    if payload.name is not None:
        series.name = payload.name
    if payload.num_episodes is not None:
        series.num_episodes = payload.num_episodes
    if payload.release_date is not None:
        series.release_date = payload.release_date
    if payload.adp_language_language_code is not None:
        series.adp_language_language_code = payload.adp_language_language_code
    if payload.origin_country is not None:
        series.origin_country = payload.origin_country
    if payload.description is not None:
        series.description = payload.description
    if payload.maturity_rating is not None:
        series.maturity_rating = payload.maturity_rating
    if payload.poster_url is not None:
        series.poster_url = payload.poster_url
    if payload.banner_url is not None:
        series.banner_url = payload.banner_url

    series.updated_at = datetime.utcnow()
    db.commit()

    return get_series_detail(series.series_id, db)


# -------------------------------------------------------------------------
# DELETE SERIES (ADMIN)
# -------------------------------------------------------------------------

@router.delete("/{series_id}", status_code=204)
def delete_series(
    series_id: int,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Delete a series (admin only)."""
    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    # Delete related records
    db.query(ADPSeriesGenre).filter(ADPSeriesGenre.adp_series_series_id == series_id).delete()
    db.query(ADPSeriesDub).filter(ADPSeriesDub.adp_series_series_id == series_id).delete()
    db.query(ADPSeriesSub).filter(ADPSeriesSub.adp_series_series_id == series_id).delete()
    db.query(ADPFeedback).filter(ADPFeedback.adp_series_series_id == series_id).delete()
    db.query(ADPEpisode).filter(ADPEpisode.adp_series_series_id == series_id).delete()

    db.delete(series)
    db.commit()
