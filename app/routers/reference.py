from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import ADPLanguage, ADPSeriesType, ADPCountry
from ..schemas import LanguageResponse, GenreResponse, CountryResponse

router = APIRouter()


@router.get("/languages", response_model=List[LanguageResponse])
def get_languages(db: Session = Depends(get_db)):
    languages = db.query(ADPLanguage).order_by(ADPLanguage.language_name).all()
    return [LanguageResponse(language_code=l.language_code, language_name=l.language_name) for l in languages]


@router.get("/genres", response_model=List[GenreResponse])
def get_genres(db: Session = Depends(get_db)):
    genres = db.query(ADPSeriesType).order_by(ADPSeriesType.type_name).all()
    return [GenreResponse(type_code=g.type_code, type_name=g.type_name) for g in genres]


@router.get("/countries", response_model=List[CountryResponse])
def get_countries(db: Session = Depends(get_db)):
    countries = db.query(ADPCountry).order_by(ADPCountry.country_name).all()
    return [CountryResponse(country_code=c.country_code, country_name=c.country_name) for c in countries]
