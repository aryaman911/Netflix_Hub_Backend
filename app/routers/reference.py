# app/routers/reference.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ADPCountry, ADPLanguage, ADPSeriesType, ADPUser
from app.schemas import CountryRead, CountryCreate, LanguageRead, LanguageCreate, GenreRead, GenreCreate
from app.deps import require_admin

router = APIRouter()


# =========================================================================
# COUNTRIES
# =========================================================================

@router.get("/countries", response_model=List[CountryRead])
def list_countries(db: Session = Depends(get_db)):
    """List all countries."""
    return db.query(ADPCountry).order_by(ADPCountry.country_name).all()


@router.get("/countries/{country_code}", response_model=CountryRead)
def get_country(country_code: str, db: Session = Depends(get_db)):
    """Get a country by code."""
    country = db.query(ADPCountry).filter(ADPCountry.country_code == country_code).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country


@router.post("/countries", response_model=CountryRead, status_code=201)
def create_country(
    payload: CountryCreate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Create a new country (admin only)."""
    existing = db.query(ADPCountry).filter(ADPCountry.country_code == payload.country_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Country code already exists")

    country = ADPCountry(
        country_code=payload.country_code,
        country_name=payload.country_name,
    )
    db.add(country)
    db.commit()
    db.refresh(country)
    return country


# =========================================================================
# LANGUAGES
# =========================================================================

@router.get("/languages", response_model=List[LanguageRead])
def list_languages(db: Session = Depends(get_db)):
    """List all languages."""
    return db.query(ADPLanguage).order_by(ADPLanguage.language_name).all()


@router.get("/languages/{language_code}", response_model=LanguageRead)
def get_language(language_code: str, db: Session = Depends(get_db)):
    """Get a language by code."""
    language = db.query(ADPLanguage).filter(ADPLanguage.language_code == language_code).first()
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")
    return language


@router.post("/languages", response_model=LanguageRead, status_code=201)
def create_language(
    payload: LanguageCreate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Create a new language (admin only)."""
    existing = db.query(ADPLanguage).filter(ADPLanguage.language_code == payload.language_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Language code already exists")

    language = ADPLanguage(
        language_code=payload.language_code,
        language_name=payload.language_name,
    )
    db.add(language)
    db.commit()
    db.refresh(language)
    return language


# =========================================================================
# GENRES (Series Types)
# =========================================================================

@router.get("/genres", response_model=List[GenreRead])
def list_genres(db: Session = Depends(get_db)):
    """List all genres/series types."""
    return db.query(ADPSeriesType).order_by(ADPSeriesType.type_name).all()


@router.get("/genres/{type_code}", response_model=GenreRead)
def get_genre(type_code: str, db: Session = Depends(get_db)):
    """Get a genre by code."""
    genre = db.query(ADPSeriesType).filter(ADPSeriesType.type_code == type_code).first()
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return genre


@router.post("/genres", response_model=GenreRead, status_code=201)
def create_genre(
    payload: GenreCreate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Create a new genre (admin only)."""
    existing = db.query(ADPSeriesType).filter(ADPSeriesType.type_code == payload.type_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Genre code already exists")

    genre = ADPSeriesType(
        type_code=payload.type_code,
        type_name=payload.type_name,
    )
    db.add(genre)
    db.commit()
    db.refresh(genre)
    return genre
