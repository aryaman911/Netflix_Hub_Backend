# app/routers/reference.py

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ADPLanguage, ADPSeriesType, ADPCountry
from app.schemas import LanguageItem, GenreItem, CountryItem

router = APIRouter()


@router.get("/languages", response_model=List[LanguageItem])
def list_languages(db: Session = Depends(get_db)):
    """Get all available languages."""
    rows = db.query(ADPLanguage).order_by(ADPLanguage.language_name).all()
    return [
        LanguageItem(language_code=r.language_code, language_name=r.language_name)
        for r in rows
    ]


@router.get("/genres", response_model=List[GenreItem])
def list_genres(db: Session = Depends(get_db)):
    """Get all available genres/series types."""
    rows = db.query(ADPSeriesType).order_by(ADPSeriesType.type_name).all()
    return [
        GenreItem(type_code=r.type_code, type_name=r.type_name)
        for r in rows
    ]


@router.get("/countries", response_model=List[CountryItem])
def list_countries(db: Session = Depends(get_db)):
    """Get all available countries."""
    rows = db.query(ADPCountry).order_by(ADPCountry.country_name).all()
    return [
        CountryItem(country_code=r.country_code, country_name=r.country_name)
        for r in rows
    ]
