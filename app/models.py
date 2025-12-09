# app/models.py

from datetime import datetime, date
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
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


# ===========================================================================
# USER & AUTHENTICATION TABLES
# ===========================================================================

class ADPUser(Base):
    """Core user table for authentication."""
    __tablename__ = "adp_user"

    user_id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    last_login_at = Column(DateTime(timezone=True))

    # Relationships
    roles = relationship("ADPUserRole", back_populates="user")
    account = relationship("ADPAccount", back_populates="user", uselist=False)
    employee = relationship("ADPEmployee", back_populates="user", uselist=False)
    login_audits = relationship("ADPLoginAudit", back_populates="user")
    password_resets = relationship("ADPPasswordReset", back_populates="user")


class ADPRole(Base):
    """Role definitions (ADMIN, USER, EMPLOYEE, etc.)."""
    __tablename__ = "adp_role"

    role_code = Column(String, primary_key=True)
    role_name = Column(String, nullable=False)

    # Relationships
    users = relationship("ADPUserRole", back_populates="role")


class ADPUserRole(Base):
    """Many-to-many mapping between users and roles."""
    __tablename__ = "adp_user_role"

    user_id = Column(BigInteger, ForeignKey("adp_user.user_id"), primary_key=True)
    role_code = Column(String, ForeignKey("adp_role.role_code"), primary_key=True)

    # Relationships
    user = relationship("ADPUser", back_populates="roles")
    role = relationship("ADPRole", back_populates="users")


class ADPLoginAudit(Base):
    """Tracks login attempts for security auditing."""
    __tablename__ = "adp_login_audit"

    audit_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("adp_user.user_id"), nullable=False)
    login_time = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    success = Column(Boolean, nullable=False)
    client_ip = Column(String)
    user_agent = Column(String)

    # Relationships
    user = relationship("ADPUser", back_populates="login_audits")


class ADPPasswordReset(Base):
    """Password reset tokens."""
    __tablename__ = "adp_password_reset"

    token_id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(BigInteger, ForeignKey("adp_user.user_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("ADPUser", back_populates="password_resets")


# ===========================================================================
# EMPLOYEE TABLE
# ===========================================================================

class ADPEmployee(Base):
    """Employee information linked to user accounts."""
    __tablename__ = "adp_employee"

    employee_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("adp_user.user_id"), nullable=False, unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    job_title = Column(String)
    hired_date = Column(Date, nullable=False, default=date.today)
    is_manager = Column(Boolean, nullable=False, default=False)

    # Relationships
    user = relationship("ADPUser", back_populates="employee")


# ===========================================================================
# ACCOUNT / VIEWER TABLE
# ===========================================================================

class ADPAccount(Base):
    """Customer/viewer accounts (subscribers)."""
    __tablename__ = "adp_account"

    account_id = Column(BigInteger, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    address_line1 = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state_province = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    opened_date = Column(Date, nullable=False)
    monthly_service_fee = Column(Numeric, nullable=False)
    adp_country_country_code = Column(String, ForeignKey("adp_country.country_code"), nullable=False)
    adp_user_user_id = Column(BigInteger, ForeignKey("adp_user.user_id"), nullable=False, unique=True)

    # Relationships
    user = relationship("ADPUser", back_populates="account")
    country = relationship("ADPCountry")
    feedbacks = relationship("ADPFeedback", back_populates="account")
    watchlist_items = relationship("ADPWatchlist", back_populates="account")
    view_history = relationship("ADPViewHistory", back_populates="account")


# ===========================================================================
# REFERENCE TABLES (Country, Language, Genre Types)
# ===========================================================================

class ADPCountry(Base):
    """Country reference table."""
    __tablename__ = "adp_country"

    country_code = Column(String, primary_key=True)
    country_name = Column(String, nullable=False)


class ADPLanguage(Base):
    """Language reference table."""
    __tablename__ = "adp_language"

    language_code = Column(String, primary_key=True)
    language_name = Column(String, nullable=False)


class ADPSeriesType(Base):
    """Genre/type reference table (Action, Drama, Comedy, etc.)."""
    __tablename__ = "adp_series_type"

    type_code = Column(String, primary_key=True)
    type_name = Column(String, nullable=False)


# ===========================================================================
# SERIES & EPISODES
# ===========================================================================

class ADPSeries(Base):
    """TV series/movies."""
    __tablename__ = "adp_series"

    series_id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    num_episodes = Column(Integer, nullable=False)
    release_date = Column(Date, nullable=False)
    adp_language_language_code = Column(String, ForeignKey("adp_language.language_code"), nullable=False)
    origin_country = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    description = Column(Text)
    maturity_rating = Column(String)
    poster_url = Column(Text)
    banner_url = Column(Text)
    average_rating = Column(Numeric, nullable=False, default=0)  # Denormalized
    rating_count = Column(Integer, nullable=False, default=0)    # Denormalized

    # Relationships
    language = relationship("ADPLanguage")
    episodes = relationship("ADPEpisode", back_populates="series")
    genres = relationship("ADPSeriesGenre", back_populates="series")
    dubs = relationship("ADPSeriesDub", back_populates="series")
    subs = relationship("ADPSeriesSub", back_populates="series")
    feedbacks = relationship("ADPFeedback", back_populates="series")
    watchlist_entries = relationship("ADPWatchlist", back_populates="series")
    countries = relationship("ADPSeriesCountry", back_populates="series")
    contracts = relationship("ADPContract", back_populates="series")


class ADPEpisode(Base):
    """Episodes belonging to a series."""
    __tablename__ = "adp_episode"

    episode_id = Column(BigInteger, primary_key=True)
    episode_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), nullable=False)
    total_viewers = Column(BigInteger, nullable=False, default=0)
    tech_interrupt_yn = Column(String(1), nullable=False, default='N')
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    synopsis = Column(Text)
    runtime_minutes = Column(Integer)

    # Relationships
    series = relationship("ADPSeries", back_populates="episodes")
    view_history = relationship("ADPViewHistory", back_populates="episode")
    schedules = relationship("ADPSchedule", back_populates="episode")


class ADPSeriesGenre(Base):
    """Many-to-many: Series to Genre types."""
    __tablename__ = "adp_series_genre"

    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    adp_series_type_type_code = Column(String, ForeignKey("adp_series_type.type_code"), primary_key=True)

    # Relationships
    series = relationship("ADPSeries", back_populates="genres")
    type = relationship("ADPSeriesType")


class ADPSeriesDub(Base):
    """Many-to-many: Series to dub languages."""
    __tablename__ = "adp_series_dub"

    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    adp_language_language_code = Column(String, ForeignKey("adp_language.language_code"), primary_key=True)

    # Relationships
    series = relationship("ADPSeries", back_populates="dubs")
    language = relationship("ADPLanguage")


class ADPSeriesSub(Base):
    """Many-to-many: Series to subtitle languages."""
    __tablename__ = "adp_series_sub"

    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    adp_language_language_code = Column(String, ForeignKey("adp_language.language_code"), primary_key=True)

    # Relationships
    series = relationship("ADPSeries", back_populates="subs")
    language = relationship("ADPLanguage")


class ADPSeriesCountry(Base):
    """Many-to-many: Series availability by country."""
    __tablename__ = "adp_series_country"

    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    adp_country_country_code = Column(String, ForeignKey("adp_country.country_code"), primary_key=True)
    local_release_date = Column(Date, nullable=False)

    # Relationships
    series = relationship("ADPSeries", back_populates="countries")
    country = relationship("ADPCountry")


# ===========================================================================
# USER ACTIVITY (Feedback, Watchlist, View History)
# ===========================================================================

class ADPFeedback(Base):
    """User ratings and reviews for series."""
    __tablename__ = "adp_feedback"
    __table_args__ = (
        UniqueConstraint("adp_account_account_id", "adp_series_series_id", name="adp_feedback_pk"),
    )

    adp_account_account_id = Column(BigInteger, ForeignKey("adp_account.account_id"), primary_key=True)
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    feedback_text = Column(String)
    rating = Column(SmallInteger, nullable=False)
    feedback_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    account = relationship("ADPAccount", back_populates="feedbacks")
    series = relationship("ADPSeries", back_populates="feedbacks")


class ADPWatchlist(Base):
    """User watchlists."""
    __tablename__ = "adp_watchlist"
    __table_args__ = (
        UniqueConstraint("adp_account_account_id", "adp_series_series_id", name="adp_watchlist_pkey"),
    )

    adp_account_account_id = Column(BigInteger, ForeignKey("adp_account.account_id"), primary_key=True)
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    added_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    account = relationship("ADPAccount", back_populates="watchlist_items")
    series = relationship("ADPSeries", back_populates="watchlist_entries")


class ADPViewHistory(Base):
    """Tracks what users have watched."""
    __tablename__ = "adp_view_history"

    view_id = Column(BigInteger, primary_key=True)
    adp_account_account_id = Column(BigInteger, ForeignKey("adp_account.account_id"), nullable=False)
    adp_episode_episode_id = Column(BigInteger, ForeignKey("adp_episode.episode_id"), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime(timezone=True))
    watch_status = Column(String, nullable=False)  # STARTED, IN_PROGRESS, FINISHED

    # Relationships
    account = relationship("ADPAccount", back_populates="view_history")
    episode = relationship("ADPEpisode", back_populates="view_history")


# ===========================================================================
# SCHEDULING
# ===========================================================================

class ADPSchedule(Base):
    """Episode broadcast schedules."""
    __tablename__ = "adp_schedule"

    schedule_id = Column(BigInteger, primary_key=True)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    adp_episode_episode_id = Column(BigInteger, ForeignKey("adp_episode.episode_id"), nullable=False)

    # Relationships
    episode = relationship("ADPEpisode", back_populates="schedules")


# ===========================================================================
# PRODUCTION (Contracts, Production Houses, Producers)
# ===========================================================================

class ADPProductionHouse(Base):
    """Production companies/studios."""
    __tablename__ = "adp_production_house"

    house_id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    address_line1 = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state_province = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    year_established = Column(Integer, nullable=False)
    adp_country_country_code = Column(String, ForeignKey("adp_country.country_code"), nullable=False)

    # Relationships
    country = relationship("ADPCountry")
    contracts = relationship("ADPContract", back_populates="production_house")
    producers = relationship("ADPProducerHouse", back_populates="production_house")


class ADPProducer(Base):
    """Individual producers."""
    __tablename__ = "adp_producer"

    producer_id = Column(BigInteger, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address_line1 = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state_province = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    adp_country_country_code = Column(String, ForeignKey("adp_country.country_code"), nullable=False)

    # Relationships
    country = relationship("ADPCountry")
    houses = relationship("ADPProducerHouse", back_populates="producer")


class ADPProducerHouse(Base):
    """Many-to-many: Producers to Production Houses."""
    __tablename__ = "adp_producer_house"

    adp_producer_producer_id = Column(BigInteger, ForeignKey("adp_producer.producer_id"), primary_key=True)
    adp_production_house_house_id = Column(BigInteger, ForeignKey("adp_production_house.house_id"), primary_key=True)
    role_desc = Column(String)

    # Relationships
    producer = relationship("ADPProducer", back_populates="houses")
    production_house = relationship("ADPProductionHouse", back_populates="producers")


class ADPContract(Base):
    """Contracts between production houses and series."""
    __tablename__ = "adp_contract"

    contract_id = Column(BigInteger, primary_key=True)
    contract_start_date = Column(Date, nullable=False)
    contract_end_date = Column(Date, nullable=False)
    per_episode_charge = Column(Numeric, nullable=False)
    status = Column(String, nullable=False)  # ACTIVE, COMPLETED, TERMINATED
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), nullable=False)
    adp_production_house_house_id = Column(BigInteger, ForeignKey("adp_production_house.house_id"), nullable=False)

    # Relationships
    series = relationship("ADPSeries", back_populates="contracts")
    production_house = relationship("ADPProductionHouse", back_populates="contracts")
