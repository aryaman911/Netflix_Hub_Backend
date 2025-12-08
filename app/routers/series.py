from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.database import get_db
from app.models import (
    ADPSeries,
    ADPSeriesGenre,
    ADPSeriesType,
    ADPLanguage,
    ADPFeedback,
    ADPEpisode,
)
from app.schemas import SeriesListItem, SeriesDetail, SeriesCreate, SeriesUpdate, Episode
from app.deps import require_admin, get_current_user
from app.models import ADPUser

router = APIRouter(prefix="/series", tags=["series"])


@router.get("/", response_model=List[SeriesListItem])
def list_series(
    search: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),        # type_code
    language: Optional[str] = Query(None),     # language_code
    db: Session = Depends(get_db),
):
    q = db.query(
        ADPSeries.series_id,
        ADPSeries.name,
        ADPSeries.poster_url,
        ADPSeries.maturity_rating,
        ADPSeries.origin_country,
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
            language_code=row.language_code,
            avg_rating=float(row.avg_rating) if row.avg_rating is not None else None,
        )
        for row in rows
    ]


@router.get("/{series_id}", response_model=SeriesDetail)
def get_series_detail(series_id: int, db: Session = Depends(get_db)):
    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    # genres, dubs, subs
    genre_rows = (
        db.query(ADPSeriesType.type_code)
        .join(ADPSeriesGenre, ADPSeriesGenre.adp_series_type_type_code == ADPSeriesType.type_code)
        .filter(ADPSeriesGenre.adp_series_series_id == series_id)
        .all()
    )
    genres = [g.type_code for g in genre_rows]

    dub_rows = (
        db.query(ADPLanguage.language_code)
        .join(ADPSeriesDub, ADPSeriesDub.adp_language_language_code == ADPLanguage.language_code)
        .filter(ADPSeriesDub.adp_series_series_id == series_id)
        .all()
    )
    dub_langs = [d.language_code for d in dub_rows]

    sub_rows = (
        db.query(ADPLanguage.language_code)
        .join(ADPSeriesSub, ADPSeriesSub.adp_language_language_code == ADPLanguage.language_code)
        .filter(ADPSeriesSub.adp_series_series_id == series_id)
        .all()
    )
    sub_langs = [s.language_code for s in sub_rows]

    avg_rating = (
        db.query(func.avg(ADPFeedback.rating))
        .filter(ADPFeedback.adp_series_series_id == series_id)
        .scalar()
    )

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
        language_code=series.adp_language_language_code,
        genres=genres,
        dub_languages=dub_langs,
        sub_languages=sub_langs,
        avg_rating=float(avg_rating) if avg_rating is not None else None,
        episodes=[Episode.model_validate(ep) for ep in eps],
    )


@router.post("/", response_model=SeriesDetail)
def create_series(
    payload: SeriesCreate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    # generate series_id manually if not identity
    from sqlalchemy import func

    max_id = db.query(func.max(ADPSeries.series_id)).scalar()
    next_id = (max_id or 0) + 1

    series = ADPSeries(
        series_id=next_id,
        name=payload.name,
        num_episodes=payload.num_episodes,
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
    for g in payload.genre_codes:
        db.add(ADPSeriesGenre(adp_series_series_id=series.series_id, adp_series_type_type_code=g))

    # dubs
    for lang in payload.dub_language_codes:
        db.add(ADPSeriesDub(adp_series_series_id=series.series_id, adp_language_language_code=lang))

    # subs
    for lang in payload.sub_language_codes:
        db.add(ADPSeriesSub(adp_series_series_id=series.series_id, adp_language_language_code=lang))

    db.commit()
    db.refresh(series)

    return get_series_detail(series.series_id, db=db)


@router.patch("/{series_id}", response_model=SeriesDetail)
def update_series(
    series_id: int,
    payload: SeriesUpdate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
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

    db.commit()
    db.refresh(series)

    return get_series_detail(series.series_id, db=db)