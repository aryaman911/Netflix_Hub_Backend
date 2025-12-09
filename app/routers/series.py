# app/routers/series.py

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
    ADPFeedback,
    ADPEpisode,
    ADPSeriesDub,   # FIXED: Added missing import
    ADPSeriesSub,   # FIXED: Added missing import
    ADPUser,
)
from app.schemas import SeriesListItem, SeriesDetail, SeriesCreate, SeriesUpdate, Episode
from app.deps import require_admin

# FIXED: Removed prefix="/series" - it's now set in main.py only
router = APIRouter()


@router.get("/", response_model=List[SeriesListItem])
def list_series(
    search: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),        # type_code
    language: Optional[str] = Query(None),     # language_code
    db: Session = Depends(get_db),
):
    """List all series with optional filters."""
    q = db.query(
        ADPSeries.series_id,
        ADPSeries.name,
        ADPSeries.poster_url,
        ADPSeries.maturity_rating,
        ADPSeries.origin_country,
        ADPSeries.release_date,
        ADPSeries.adp_language_language_code.label("language_code"),
        func.avg(ADPFeedback.rating).label("avg_rating"),
    ).outerjoin(ADPFeedback, ADPFeedback.adp_series_series_id == ADPSeries.series_id)

    if search:
        ilike = f"%{search.lower()}%"
        q = q.filter(func.lower(ADPSeries.name).like(ilike))

    if language:
        q = q.filter(ADPSeries.adp_language_language_code == language)

    if genre:
        q = q.join(ADPSeriesGenre, ADPSeriesGenre.adp_series_series_id == ADPSeries.series_id)
        q = q.filter(ADPSeriesGenre.adp_series_type_type_code == genre)

    q = q.group_by(
        ADPSeries.series_id,
        ADPSeries.name,
        ADPSeries.poster_url,
        ADPSeries.maturity_rating,
        ADPSeries.origin_country,
        ADPSeries.release_date,
        ADPSeries.adp_language_language_code,
    )

    rows = q.all()
    return [
        SeriesListItem(
            series_id=row.series_id,
            name=row.name,
            poster_url=row.poster_url,
            maturity_rating=row.maturity_rating,
            origin_country=row.origin_country,
            release_date=row.release_date,
            language_code=row.language_code,
            avg_rating=float(row.avg_rating) if row.avg_rating is not None else None,
        )
        for row in rows
    ]


@router.get("/{series_id}", response_model=SeriesDetail)
def get_series_detail(series_id: int, db: Session = Depends(get_db)):
    """Get detailed info for a single series."""
    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    # genres
    genre_rows = (
        db.query(ADPSeriesType.type_code)
        .join(ADPSeriesGenre, ADPSeriesGenre.adp_series_type_type_code == ADPSeriesType.type_code)
        .filter(ADPSeriesGenre.adp_series_series_id == series_id)
        .all()
    )
    genres = [g.type_code for g in genre_rows]

    # dubs
    dub_rows = (
        db.query(ADPLanguage.language_code)
        .join(ADPSeriesDub, ADPSeriesDub.adp_language_language_code == ADPLanguage.language_code)
        .filter(ADPSeriesDub.adp_series_series_id == series_id)
        .all()
    )
    dub_langs = [d.language_code for d in dub_rows]

    # subs
    sub_rows = (
        db.query(ADPLanguage.language_code)
        .join(ADPSeriesSub, ADPSeriesSub.adp_language_language_code == ADPLanguage.language_code)
        .filter(ADPSeriesSub.adp_series_series_id == series_id)
        .all()
    )
    sub_langs = [s.language_code for s in sub_rows]

    # average rating and count
    rating_result = (
        db.query(
            func.avg(ADPFeedback.rating).label("avg"),
            func.count(ADPFeedback.rating).label("count")
        )
        .filter(ADPFeedback.adp_series_series_id == series_id)
        .first()
    )
    avg_rating = float(rating_result.avg) if rating_result.avg else None
    rating_count = rating_result.count or 0

    # episodes
    eps = (
        db.query(ADPEpisode)
        .filter(ADPEpisode.adp_series_series_id == series_id)
        .order_by(ADPEpisode.episode_number)
        .all()
    )

    return SeriesDetail(
        series_id=series.series_id,
        name=series.name,
        description=series.description,
        maturity_rating=series.maturity_rating,
        poster_url=series.poster_url,
        banner_url=series.banner_url,
        release_date=series.release_date,
        origin_country=series.origin_country,
        num_episodes=series.num_episodes,
        language_code=series.adp_language_language_code,
        genres=genres,
        dub_languages=dub_langs,
        sub_languages=sub_langs,
        avg_rating=avg_rating,
        rating_count=rating_count,
        episodes=[
            Episode(
                episode_id=ep.episode_id,
                episode_number=ep.episode_number,
                title=ep.title,
                synopsis=ep.synopsis,
                runtime_minutes=ep.runtime_minutes,
            )
            for ep in eps
        ],
    )


@router.post("/", response_model=SeriesDetail)
def create_series(
    payload: SeriesCreate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Create a new series (admin only)."""
    # generate series_id manually
    max_id = db.query(func.max(ADPSeries.series_id)).scalar()
    next_id = (max_id or 0) + 1

    series = ADPSeries(
        series_id=next_id,
        name=payload.name,
        num_episodes=payload.num_episodes or 0,
        release_date=payload.release_date,
        adp_language_language_code=payload.language_code,
        origin_country=payload.origin_country,
        description=payload.description,
        maturity_rating=payload.maturity_rating,
        poster_url=payload.poster_url,
        banner_url=payload.banner_url,
    )
    db.add(series)

    # genres
    if payload.genre_codes:
        for g in payload.genre_codes:
            db.add(ADPSeriesGenre(adp_series_series_id=series.series_id, adp_series_type_type_code=g))

    # dubs
    if payload.dub_language_codes:
        for lang in payload.dub_language_codes:
            db.add(ADPSeriesDub(adp_series_series_id=series.series_id, adp_language_language_code=lang))

    # subs
    if payload.sub_language_codes:
        for lang in payload.sub_language_codes:
            db.add(ADPSeriesSub(adp_series_series_id=series.series_id, adp_language_language_code=lang))

    db.commit()
    db.refresh(series)

    return get_series_detail(series.series_id, db=db)


@router.put("/{series_id}", response_model=SeriesDetail)
def update_series_put(
    series_id: int,
    payload: SeriesUpdate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Update a series (admin only) - PUT method."""
    return _update_series(series_id, payload, db)


@router.patch("/{series_id}", response_model=SeriesDetail)
def update_series_patch(
    series_id: int,
    payload: SeriesUpdate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Update a series (admin only) - PATCH method."""
    return _update_series(series_id, payload, db)


def _update_series(series_id: int, payload: SeriesUpdate, db: Session) -> SeriesDetail:
    """Internal helper for updating series."""
    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    if payload.name is not None:
        series.name = payload.name
    if payload.description is not None:
        series.description = payload.description
    if payload.maturity_rating is not None:
        series.maturity_rating = payload.maturity_rating
    if payload.poster_url is not None:
        series.poster_url = payload.poster_url
    if payload.banner_url is not None:
        series.banner_url = payload.banner_url
    if payload.origin_country is not None:
        series.origin_country = payload.origin_country
    if payload.language_code is not None:
        series.adp_language_language_code = payload.language_code
    if payload.num_episodes is not None:
        series.num_episodes = payload.num_episodes
    if payload.release_date is not None:
        series.release_date = payload.release_date

    db.commit()
    db.refresh(series)

    return get_series_detail(series.series_id, db=db)


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

    # Delete related records first
    db.query(ADPSeriesGenre).filter(ADPSeriesGenre.adp_series_series_id == series_id).delete()
    db.query(ADPSeriesDub).filter(ADPSeriesDub.adp_series_series_id == series_id).delete()
    db.query(ADPSeriesSub).filter(ADPSeriesSub.adp_series_series_id == series_id).delete()
    db.query(ADPFeedback).filter(ADPFeedback.adp_series_series_id == series_id).delete()
    db.query(ADPEpisode).filter(ADPEpisode.adp_series_series_id == series_id).delete()

    db.delete(series)
    db.commit()
