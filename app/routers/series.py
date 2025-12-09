from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import ADPSeries, ADPSeriesGenre, ADPSeriesType, ADPEpisode
from ..schemas import SeriesCreate, SeriesUpdate, SeriesResponse, EpisodeResponse
from ..deps import get_current_user, require_admin

router = APIRouter()


def serialize_series(s: ADPSeries) -> dict:
    return {
        "series_id": s.series_id,
        "name": s.name,
        "num_episodes": s.num_episodes,
        "release_date": s.release_date,
        "language_code": s.adp_language_language_code,
        "origin_country": s.origin_country,
        "description": s.description,
        "maturity_rating": s.maturity_rating,
        "poster_url": s.poster_url,
        "banner_url": s.banner_url,
        "avg_rating": float(s.average_rating) if s.average_rating else None,
        "rating_count": s.rating_count or 0,
        "genres": [g.type.type_name for g in s.genres if g.type],
        "episodes": [
            {
                "episode_id": e.episode_id,
                "episode_number": e.episode_number,
                "title": e.title,
                "synopsis": e.synopsis,
                "runtime_minutes": e.runtime_minutes,
            }
            for e in sorted(s.episodes, key=lambda x: x.episode_number)
        ] if s.episodes else [],
    }


@router.get("", response_model=List[SeriesResponse])
def get_series(
    search: Optional[str] = None,
    genre: Optional[str] = None,
    language: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(ADPSeries)
    
    if search:
        query = query.filter(ADPSeries.name.ilike(f"%{search}%"))
    
    if language:
        query = query.filter(ADPSeries.adp_language_language_code == language)
    
    if genre:
        query = query.join(ADPSeriesGenre).filter(
            ADPSeriesGenre.adp_series_type_type_code == genre
        )
    
    series_list = query.order_by(ADPSeries.average_rating.desc()).all()
    return [serialize_series(s) for s in series_list]


@router.get("/{series_id}", response_model=SeriesResponse)
def get_series_by_id(series_id: int, db: Session = Depends(get_db)):
    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return serialize_series(series)


@router.post("", response_model=SeriesResponse, status_code=201)
def create_series(
    series_in: SeriesCreate,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    try:
        # Get next ID with lock
        max_id = db.query(func.max(ADPSeries.series_id)).with_for_update().scalar()
        next_id = (max_id or 0) + 1
        
        series = ADPSeries(
            series_id=next_id,
            name=series_in.name,
            num_episodes=series_in.num_episodes,
            release_date=series_in.release_date,
            adp_language_language_code=series_in.language_code,
            origin_country=series_in.origin_country,
            description=series_in.description,
            maturity_rating=series_in.maturity_rating,
            poster_url=series_in.poster_url,
            banner_url=series_in.banner_url,
        )
        db.add(series)
        
        # Add genres
        for code in series_in.genre_codes:
            genre = ADPSeriesGenre(
                adp_series_series_id=next_id,
                adp_series_type_type_code=code,
            )
            db.add(genre)
        
        db.commit()
        db.refresh(series)
        return serialize_series(series)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{series_id}", response_model=SeriesResponse)
def update_series(
    series_id: int,
    series_in: SeriesUpdate,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    # Lock row for update
    series = db.query(ADPSeries).filter(
        ADPSeries.series_id == series_id
    ).with_for_update().first()
    
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    try:
        if series_in.name is not None:
            series.name = series_in.name
        if series_in.release_date is not None:
            series.release_date = series_in.release_date
        if series_in.language_code is not None:
            series.adp_language_language_code = series_in.language_code
        if series_in.origin_country is not None:
            series.origin_country = series_in.origin_country
        if series_in.num_episodes is not None:
            series.num_episodes = series_in.num_episodes
        if series_in.description is not None:
            series.description = series_in.description
        if series_in.maturity_rating is not None:
            series.maturity_rating = series_in.maturity_rating
        if series_in.poster_url is not None:
            series.poster_url = series_in.poster_url
        if series_in.banner_url is not None:
            series.banner_url = series_in.banner_url
        
        # Update genres if provided
        if series_in.genre_codes is not None:
            db.query(ADPSeriesGenre).filter(
                ADPSeriesGenre.adp_series_series_id == series_id
            ).delete()
            for code in series_in.genre_codes:
                genre = ADPSeriesGenre(
                    adp_series_series_id=series_id,
                    adp_series_type_type_code=code,
                )
                db.add(genre)
        
        db.commit()
        db.refresh(series)
        return serialize_series(series)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{series_id}", status_code=204)
def delete_series(
    series_id: int,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    series = db.query(ADPSeries).filter(
        ADPSeries.series_id == series_id
    ).with_for_update().first()
    
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    try:
        db.delete(series)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
