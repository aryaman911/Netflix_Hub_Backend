# app/models.py

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Boolean,
    Text,
    Date,
    ForeignKey,
    SmallInteger,
    Numeric,
    UniqueConstraint,
    DateTime,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ============================================================================
# REFERENCE TABLES
# ============================================================================

class ADPCountry(Base):
    __tablename__ = "adp_country"
    
    country_code = Column(String(3), primary_key=True)
    country_name = Column(String(100), nullable=False)


class ADPLanguage(Base):
    __tablename__ = "adp_language"
    
    language_code = Column(String(5), primary_key=True)
    language_name = Column(String(50), nullable=False)


class ADPSeriesType(Base):
    __tablename__ = "adp_series_type"
    
    type_code = Column(String(20), primary_key=True)
    type_name = Column(String(50), nullable=False)


class ADPRole(Base):
    __tablename__ = "adp_role"
    
    role_code = Column(String(20), primary_key=True)
    role_name = Column(String(50), nullable=False)
    
    users = relationship("ADPUserRole", back_populates="role")


# ============================================================================
# USER / AUTH TABLES
# ============================================================================

class ADPUser(Base):
    __tablename__ = "adp_user"
    
    user_id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime(timezone=True))
    
    roles = relationship("ADPUserRole", back_populates="user")
    account = relationship("ADPAccount", back_populates="user", uselist=False)
    employee = relationship("ADPEmployee", back_populates="user", uselist=False)


class ADPUserRole(Base):
    __tablename__ = "adp_user_role"
    
    user_id = Column(BigInteger, ForeignKey("adp_user.user_id"), primary_key=True)
    role_code = Column(String(20), ForeignKey("adp_role.role_code"), primary_key=True)
    
    user = relationship("ADPUser", back_populates="roles")
    role = relationship("ADPRole", back_populates="users")


class ADPEmployee(Base):
    __tablename__ = "adp_employee"
    
    employee_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("adp_user.user_id"), nullable=False, unique=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    job_title = Column(String(100))
    hired_date = Column(Date, nullable=False)
    is_manager = Column(Boolean, nullable=False, default=False)
    
    user = relationship("ADPUser", back_populates="employee")


class ADPAccount(Base):
    __tablename__ = "adp_account"
    
    account_id = Column(BigInteger, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    address_line1 = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state_province = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    opened_date = Column(Date, nullable=False)
    monthly_service_fee = Column(Numeric(10, 2), nullable=False, default=Decimal("9.99"))
    adp_country_country_code = Column(String(3), ForeignKey("adp_country.country_code"), nullable=False)
    adp_user_user_id = Column(BigInteger, ForeignKey("adp_user.user_id"), nullable=False, unique=True)
    
    user = relationship("ADPUser", back_populates="account")
    feedbacks = relationship("ADPFeedback", back_populates="account")
    watchlist_items = relationship("ADPWatchlist", back_populates="account")
    view_history = relationship("ADPViewHistory", back_populates="account")


class ADPLoginAudit(Base):
    __tablename__ = "adp_login_audit"
    
    audit_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("adp_user.user_id"), nullable=False)
    login_time = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    success = Column(Boolean, nullable=False, default=True)


class ADPPasswordReset(Base):
    __tablename__ = "adp_password_reset"
    
    token_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("adp_user.user_id"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))


# ============================================================================
# CONTENT TABLES
# ============================================================================

class ADPSeries(Base):
    __tablename__ = "adp_series"
    
    series_id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False)
    num_episodes = Column(Integer, nullable=False, default=0)
    release_date = Column(Date, nullable=False)
    adp_language_language_code = Column(String(5), ForeignKey("adp_language.language_code"), nullable=False)
    origin_country = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Extended columns
    description = Column(Text)
    maturity_rating = Column(String(10))
    poster_url = Column(Text)
    banner_url = Column(Text)
    
    # Denormalized rating columns (updated by trigger)
    average_rating = Column(Numeric(3, 2), default=Decimal("0"))
    rating_count = Column(Integer, default=0)
    
    # Relationships
    episodes = relationship("ADPEpisode", back_populates="series", cascade="all, delete-orphan")
    genres = relationship("ADPSeriesGenre", back_populates="series", cascade="all, delete-orphan")
    dubs = relationship("ADPSeriesDub", back_populates="series", cascade="all, delete-orphan")
    subs = relationship("ADPSeriesSub", back_populates="series", cascade="all, delete-orphan")
    feedbacks = relationship("ADPFeedback", back_populates="series", cascade="all, delete-orphan")
    watchlist_entries = relationship("ADPWatchlist", back_populates="series", cascade="all, delete-orphan")


class ADPSeriesGenre(Base):
    __tablename__ = "adp_series_genre"
    
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    adp_series_type_type_code = Column(String(20), ForeignKey("adp_series_type.type_code"), primary_key=True)
    
    series = relationship("ADPSeries", back_populates="genres")
    type = relationship("ADPSeriesType")


class ADPSeriesDub(Base):
    __tablename__ = "adp_series_dub"
    
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    adp_language_language_code = Column(String(5), ForeignKey("adp_language.language_code"), primary_key=True)
    
    series = relationship("ADPSeries", back_populates="dubs")
    language = relationship("ADPLanguage")


class ADPSeriesSub(Base):
    __tablename__ = "adp_series_sub"
    
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    adp_language_language_code = Column(String(5), ForeignKey("adp_language.language_code"), primary_key=True)
    
    series = relationship("ADPSeries", back_populates="subs")
    language = relationship("ADPLanguage")


class ADPEpisode(Base):
    __tablename__ = "adp_episode"
    
    episode_id = Column(BigInteger, primary_key=True)
    episode_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), nullable=False)
    total_viewers = Column(BigInteger, nullable=False, default=0)
    tech_interrupt_yn = Column(String(1), nullable=False, default="N")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Extended columns
    synopsis = Column(Text)
    runtime_minutes = Column(Integer)
    
    series = relationship("ADPSeries", back_populates="episodes")
    view_history = relationship("ADPViewHistory", back_populates="episode")


# ============================================================================
# USER ACTIVITY TABLES
# ============================================================================

class ADPFeedback(Base):
    __tablename__ = "adp_feedback"
    __table_args__ = (
        UniqueConstraint("adp_account_account_id", "adp_series_series_id", name="adp_feedback_pk"),
    )
    
    adp_account_account_id = Column(BigInteger, ForeignKey("adp_account.account_id"), primary_key=True)
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    feedback_text = Column(Text)
    rating = Column(SmallInteger, nullable=False)
    feedback_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    account = relationship("ADPAccount", back_populates="feedbacks")
    series = relationship("ADPSeries", back_populates="feedbacks")


class ADPWatchlist(Base):
    __tablename__ = "adp_watchlist"
    __table_args__ = (
        UniqueConstraint("adp_account_account_id", "adp_series_series_id", name="adp_watchlist_pkey"),
    )
    
    adp_account_account_id = Column(BigInteger, ForeignKey("adp_account.account_id"), primary_key=True)
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    added_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    account = relationship("ADPAccount", back_populates="watchlist_items")
    series = relationship("ADPSeries", back_populates="watchlist_entries")


class ADPViewHistory(Base):
    __tablename__ = "adp_view_history"
    
    view_id = Column(BigInteger, primary_key=True)
    adp_account_account_id = Column(BigInteger, ForeignKey("adp_account.account_id"), nullable=False)
    adp_episode_episode_id = Column(BigInteger, ForeignKey("adp_episode.episode_id"), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime(timezone=True))
    watch_status = Column(String(20), nullable=False)
    
    account = relationship("ADPAccount", back_populates="view_history")
    episode = relationship("ADPEpisode", back_populates="view_history")


# ============================================================================
# PRODUCTION TABLES
# ============================================================================

class ADPProductionHouse(Base):
    __tablename__ = "adp_production_house"
    
    house_id = Column(BigInteger, primary_key=True)
    house_name = Column(String(255), nullable=False)
    adp_country_country_code = Column(String(3), ForeignKey("adp_country.country_code"), nullable=False)


class ADPProducer(Base):
    __tablename__ = "adp_producer"
    
    producer_id = Column(BigInteger, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    adp_country_country_code = Column(String(3), ForeignKey("adp_country.country_code"), nullable=False)


class ADPContract(Base):
    __tablename__ = "adp_contract"
    
    contract_id = Column(BigInteger, primary_key=True)
    adp_production_house_house_id = Column(BigInteger, ForeignKey("adp_production_house.house_id"), nullable=False)
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), nullable=False)
    contract_start_date = Column(Date, nullable=False)
    contract_end_date = Column(Date, nullable=False)
    contract_value = Column(Numeric(15, 2))
    status = Column(String(20), nullable=False, default="ACTIVE")


class ADPSchedule(Base):
    __tablename__ = "adp_schedule"
    
    schedule_id = Column(BigInteger, primary_key=True)
    adp_episode_episode_id = Column(BigInteger, ForeignKey("adp_episode.episode_id"), nullable=False)
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    channel = Column(String(50))
