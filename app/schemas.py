# app/schemas.py - UserCreate with account fields
#
# UPDATED: UserCreate now includes all fields needed for ADPAccount

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, ConfigDict


# ===========================================================================
# BASE CONFIG
# ===========================================================================

class ORMModel(BaseModel):
    """Base model configured to read data from SQLAlchemy objects."""
    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# USER / AUTH SCHEMAS
# ===========================================================================

class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    """
    Schema for user signup.
    Includes all fields needed to create both ADPUser AND ADPAccount.
    """
    password: str
    # Account fields (linked to ADPAccount)
    first_name: str
    last_name: str
    address_line1: str
    city: str
    state_province: str
    postal_code: str
    country_code: str  # FK to adp_country


class UserRead(UserBase):
    id: int
    is_active: bool = True


class UserLogin(BaseModel):
    identifier: str  # email or username
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenWithUser(Token):
    user_id: int
    roles: List[str] = []


class TokenData(BaseModel):
    user_id: int


# Password Reset
class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: UUID
    new_password: str


class PasswordResetResponse(BaseModel):
    message: str


# Login Audit
class LoginAuditItem(ORMModel):
    audit_id: int
    user_id: int
    login_time: datetime
    success: bool
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None


# ===========================================================================
# ROLE SCHEMAS
# ===========================================================================

class RoleRead(ORMModel):
    role_code: str
    role_name: str


class UserRoleAssign(BaseModel):
    user_id: int
    role_code: str


# ===========================================================================
# EMPLOYEE SCHEMAS
# ===========================================================================

class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    job_title: Optional[str] = None
    is_manager: bool = False


class EmployeeCreate(EmployeeBase):
    user_id: int
    hired_date: Optional[date] = None


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    job_title: Optional[str] = None
    is_manager: Optional[bool] = None


class EmployeeRead(EmployeeBase, ORMModel):
    employee_id: int
    user_id: int
    hired_date: date


# ===========================================================================
# ACCOUNT SCHEMAS
# ===========================================================================

class AccountBase(BaseModel):
    first_name: str
    last_name: str
    address_line1: str
    city: str
    state_province: str
    postal_code: str
    monthly_service_fee: Decimal
    adp_country_country_code: str


class AccountCreate(AccountBase):
    adp_user_user_id: int
    opened_date: Optional[date] = None


class AccountUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    monthly_service_fee: Optional[Decimal] = None


class AccountRead(AccountBase, ORMModel):
    account_id: int
    adp_user_user_id: int
    opened_date: date


# ===========================================================================
# REFERENCE TABLE SCHEMAS (Country, Language, Genre)
# ===========================================================================

class CountryRead(ORMModel):
    country_code: str
    country_name: str


class CountryCreate(BaseModel):
    country_code: str
    country_name: str


class LanguageRead(ORMModel):
    language_code: str
    language_name: str


class LanguageCreate(BaseModel):
    language_code: str
    language_name: str


class GenreRead(ORMModel):
    type_code: str
    type_name: str


class GenreCreate(BaseModel):
    type_code: str
    type_name: str


# ===========================================================================
# EPISODE SCHEMAS
# ===========================================================================

class EpisodeBase(BaseModel):
    episode_number: int
    title: str
    synopsis: Optional[str] = None
    runtime_minutes: Optional[int] = None


class EpisodeCreate(EpisodeBase):
    adp_series_series_id: int
    total_viewers: int = 0
    tech_interrupt_yn: str = 'N'


class EpisodeUpdate(BaseModel):
    episode_number: Optional[int] = None
    title: Optional[str] = None
    synopsis: Optional[str] = None
    runtime_minutes: Optional[int] = None
    total_viewers: Optional[int] = None
    tech_interrupt_yn: Optional[str] = None


class EpisodeRead(EpisodeBase, ORMModel):
    episode_id: int
    adp_series_series_id: int
    total_viewers: int
    tech_interrupt_yn: str


# ===========================================================================
# SERIES SCHEMAS
# ===========================================================================

class SeriesBase(BaseModel):
    name: str
    num_episodes: int = 0
    release_date: date
    adp_language_language_code: str
    origin_country: str
    description: Optional[str] = None
    maturity_rating: Optional[str] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None


class SeriesCreate(SeriesBase):
    genre_codes: Optional[List[str]] = []
    dub_language_codes: Optional[List[str]] = []
    sub_language_codes: Optional[List[str]] = []


class SeriesUpdate(BaseModel):
    name: Optional[str] = None
    num_episodes: Optional[int] = None
    release_date: Optional[date] = None
    adp_language_language_code: Optional[str] = None
    origin_country: Optional[str] = None
    description: Optional[str] = None
    maturity_rating: Optional[str] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None


class SeriesListItem(ORMModel):
    series_id: int
    name: str
    poster_url: Optional[str] = None
    maturity_rating: Optional[str] = None
    origin_country: Optional[str] = None
    release_date: Optional[date] = None
    language_code: Optional[str] = None
    average_rating: Optional[float] = None
    rating_count: int = 0


class SeriesDetail(ORMModel):
    series_id: int
    name: str
    num_episodes: int
    release_date: date
    language_code: Optional[str] = None
    origin_country: str
    description: Optional[str] = None
    maturity_rating: Optional[str] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None
    average_rating: Optional[float] = None
    rating_count: int = 0
    genres: List[str] = []
    dub_languages: List[str] = []
    sub_languages: List[str] = []
    episodes: List[EpisodeRead] = []


# ===========================================================================
# FEEDBACK SCHEMAS
# ===========================================================================

class FeedbackCreate(BaseModel):
    rating: int  # 1-5
    feedback_text: Optional[str] = None


class FeedbackItem(ORMModel):
    account_id: int
    account_name: Optional[str] = None
    rating: int
    feedback_text: Optional[str] = None
    feedback_date: Optional[date] = None


class FeedbackListResponse(BaseModel):
    average_rating: Optional[float] = None
    rating_count: int = 0
    items: List[FeedbackItem] = []


# ===========================================================================
# WATCHLIST SCHEMAS
# ===========================================================================

class WatchlistItem(ORMModel):
    series_id: int
    series_name: str
    poster_url: Optional[str] = None
    added_at: Optional[datetime] = None


# ===========================================================================
# VIEW HISTORY SCHEMAS
# ===========================================================================

class ViewHistoryCreate(BaseModel):
    watch_status: str  # STARTED, IN_PROGRESS, FINISHED


class ViewHistoryItem(ORMModel):
    view_id: int
    episode_id: int
    episode_title: Optional[str] = None
    series_name: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    watch_status: str


# ===========================================================================
# SCHEDULE SCHEMAS
# ===========================================================================

class ScheduleBase(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    adp_episode_episode_id: int


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None


class ScheduleRead(ScheduleBase, ORMModel):
    schedule_id: int
    episode_title: Optional[str] = None
    series_name: Optional[str] = None


# ===========================================================================
# PRODUCTION HOUSE SCHEMAS
# ===========================================================================

class ProductionHouseBase(BaseModel):
    name: str
    address_line1: str
    city: str
    state_province: str
    postal_code: str
    year_established: int
    adp_country_country_code: str


class ProductionHouseCreate(ProductionHouseBase):
    pass


class ProductionHouseUpdate(BaseModel):
    name: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    year_established: Optional[int] = None


class ProductionHouseRead(ProductionHouseBase, ORMModel):
    house_id: int


# ===========================================================================
# PRODUCER SCHEMAS
# ===========================================================================

class ProducerBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    address_line1: str
    city: str
    state_province: str
    postal_code: str
    adp_country_country_code: str


class ProducerCreate(ProducerBase):
    pass


class ProducerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None


class ProducerRead(ProducerBase, ORMModel):
    producer_id: int


# ===========================================================================
# CONTRACT SCHEMAS
# ===========================================================================

class ContractBase(BaseModel):
    contract_start_date: date
    contract_end_date: date
    per_episode_charge: Decimal
    status: str  # ACTIVE, COMPLETED, TERMINATED
    adp_series_series_id: int
    adp_production_house_house_id: int


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    per_episode_charge: Optional[Decimal] = None
    status: Optional[str] = None


class ContractRead(ContractBase, ORMModel):
    contract_id: int
    series_name: Optional[str] = None
    production_house_name: Optional[str] = None


# ===========================================================================
# GENERIC RESPONSES
# ===========================================================================

class MessageResponse(BaseModel):
    detail: str


class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int
