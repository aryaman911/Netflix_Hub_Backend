from datetime import datetime, date
from sqlalchemy import (
    Column, BigInteger, Integer, String, Boolean, Text, Date,
    ForeignKey, SmallInteger, Numeric, DateTime, UniqueConstraint, CheckConstraint, CHAR
)
from sqlalchemy.orm import relationship
from .database import Base


class ADPUser(Base):
    __tablename__ = "adp_user"
    user_id = Column(BigInteger, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    last_login_at = Column(DateTime(timezone=True))
    
    roles = relationship("ADPUserRole", back_populates="user")
    account = relationship("ADPAccount", back_populates="user", uselist=False)


class ADPRole(Base):
    __tablename__ = "adp_role"
    role_code = Column(String, primary_key=True)
    role_name = Column(String, nullable=False)
    users = relationship("ADPUserRole", back_populates="role")


class ADPUserRole(Base):
    __tablename__ = "adp_user_role"
    user_id = Column(BigInteger, ForeignKey("adp_user.user_id"), primary_key=True)
    role_code = Column(String, ForeignKey("adp_role.role_code"), primary_key=True)
    user = relationship("ADPUser", back_populates="roles")
    role = relationship("ADPRole", back_populates="users")


class ADPCountry(Base):
    __tablename__ = "adp_country"
    country_code = Column(String(3), primary_key=True)
    country_name = Column(String(80), nullable=False, unique=True)


class ADPLanguage(Base):
    __tablename__ = "adp_language"
    language_code = Column(String(8), primary_key=True)
    language_name = Column(String(20), nullable=False, unique=True)


class ADPSeriesType(Base):
    __tablename__ = "adp_series_type"
    type_code = Column(String(16), primary_key=True)
    type_name = Column(String(40), nullable=False, unique=True)


class ADPAccount(Base):
    __tablename__ = "adp_account"
    account_id = Column(BigInteger, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    address_line1 = Column(String(120), nullable=False)
    address_line2 = Column(String(120))
    city = Column(String(80), nullable=False)
    state_province = Column(String(80), nullable=False)
    postal_code = Column(String(20), nullable=False)
    opened_date = Column(Date, nullable=False)
    monthly_service_fee = Column(Numeric(8,2), nullable=False, default=9.99)
    adp_country_country_code = Column(String(3), ForeignKey("adp_country.country_code"), nullable=False)
    adp_user_user_id = Column(BigInteger, ForeignKey("adp_user.user_id"), nullable=False, unique=True)
    
    user = relationship("ADPUser", back_populates="account")
    country = relationship("ADPCountry")
    feedbacks = relationship("ADPFeedback", back_populates="account")
    watchlist_items = relationship("ADPWatchlist", back_populates="account")


# ============================================
# PRODUCTION HOUSE & PRODUCER (Phase 1)
# ============================================

class ADPProductionHouse(Base):
    __tablename__ = "adp_production_house"
    house_id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False)
    address_line1 = Column(String(255))
    city = Column(String(100))
    state_province = Column(String(100))
    postal_code = Column(String(20))
    year_established = Column(Integer)
    adp_country_country_code = Column(String(10), ForeignKey("adp_country.country_code"))
    
    country = relationship("ADPCountry")
    contracts = relationship("ADPContract", back_populates="production_house")
    producers = relationship("ADPProducerHouse", back_populates="production_house")


class ADPProducer(Base):
    __tablename__ = "adp_producer"
    producer_id = Column(BigInteger, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    address_line1 = Column(String(255))
    city = Column(String(100))
    state_province = Column(String(100))
    postal_code = Column(String(20))
    adp_country_country_code = Column(String(10), ForeignKey("adp_country.country_code"))
    
    country = relationship("ADPCountry")
    production_houses = relationship("ADPProducerHouse", back_populates="producer")


class ADPProducerHouse(Base):
    """Bridge table: Producer <-> Production House (many-to-many)"""
    __tablename__ = "adp_producer_house"
    adp_producer_producer_id = Column(BigInteger, ForeignKey("adp_producer.producer_id"), primary_key=True)
    adp_production_house_house_id = Column(BigInteger, ForeignKey("adp_production_house.house_id"), primary_key=True)
    role_desc = Column(String(80))  # e.g., 'Executive Producer', 'Line Producer'
    
    producer = relationship("ADPProducer", back_populates="production_houses")
    production_house = relationship("ADPProductionHouse", back_populates="producers")


# ============================================
# SERIES & RELATED
# ============================================

class ADPSeries(Base):
    __tablename__ = "adp_series"
    series_id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False)
    num_episodes = Column(Integer, nullable=False, default=0)
    release_date = Column(Date, nullable=False)
    adp_language_language_code = Column(String(10), ForeignKey("adp_language.language_code"), nullable=False)
    origin_country = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    description = Column(Text)
    maturity_rating = Column(String(10))
    poster_url = Column(Text)
    banner_url = Column(Text)
    average_rating = Column(Numeric(3,2), nullable=False, default=0)
    rating_count = Column(Integer, nullable=False, default=0)
    
    language = relationship("ADPLanguage")
    genres = relationship("ADPSeriesGenre", back_populates="series", cascade="all, delete-orphan")
    dubs = relationship("ADPSeriesDub", back_populates="series", cascade="all, delete-orphan")
    subs = relationship("ADPSeriesSub", back_populates="series", cascade="all, delete-orphan")
    feedbacks = relationship("ADPFeedback", back_populates="series", cascade="all, delete-orphan")
    watchlist_entries = relationship("ADPWatchlist", back_populates="series", cascade="all, delete-orphan")
    episodes = relationship("ADPEpisode", back_populates="series", cascade="all, delete-orphan")
    contracts = relationship("ADPContract", back_populates="series")
    available_countries = relationship("ADPSeriesCountry", back_populates="series", cascade="all, delete-orphan")


class ADPSeriesCountry(Base):
    """Bridge table: Series available in multiple countries"""
    __tablename__ = "adp_series_country"
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    adp_country_country_code = Column(String(3), ForeignKey("adp_country.country_code"), primary_key=True)
    
    series = relationship("ADPSeries", back_populates="available_countries")
    country = relationship("ADPCountry")


class ADPEpisode(Base):
    __tablename__ = "adp_episode"
    episode_id = Column(BigInteger, primary_key=True)
    episode_number = Column(Integer, nullable=False)
    title = Column(String(160))
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), nullable=False)
    synopsis = Column(Text)
    runtime_minutes = Column(Integer)
    
    series = relationship("ADPSeries", back_populates="episodes")
    schedules = relationship("ADPSchedule", back_populates="episode")
    
    __table_args__ = (
        UniqueConstraint('adp_series_series_id', 'episode_number', name='uk_adp_episode_num_per_ser'),
    )


class ADPSeriesGenre(Base):
    __tablename__ = "adp_series_genre"
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    adp_series_type_type_code = Column(String(16), ForeignKey("adp_series_type.type_code"), primary_key=True)
    series = relationship("ADPSeries", back_populates="genres")
    type = relationship("ADPSeriesType")


class ADPSeriesDub(Base):
    __tablename__ = "adp_series_dub"
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    adp_language_language_code = Column(String(8), ForeignKey("adp_language.language_code"), primary_key=True)
    series = relationship("ADPSeries", back_populates="dubs")
    language = relationship("ADPLanguage")


class ADPSeriesSub(Base):
    __tablename__ = "adp_series_sub"
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    adp_language_language_code = Column(String(8), ForeignKey("adp_language.language_code"), primary_key=True)
    series = relationship("ADPSeries", back_populates="subs")
    language = relationship("ADPLanguage")


# ============================================
# CONTRACT (Phase 1)
# ============================================

class ADPContract(Base):
    __tablename__ = "adp_contract"
    contract_id = Column(BigInteger, primary_key=True)
    contract_start_date = Column(Date, nullable=False)
    contract_end_date = Column(Date)
    per_episode_charge = Column(Numeric(12,2))
    status = Column(String(20))  # ACTIVE, COMPLETED, TERMINATED, EXPIRED, SUSPENDED
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), nullable=False)
    adp_production_house_house_id = Column(BigInteger, ForeignKey("adp_production_house.house_id"))
    renewed_from_id = Column(BigInteger, ForeignKey("adp_contract.contract_id"))
    
    series = relationship("ADPSeries", back_populates="contracts")
    production_house = relationship("ADPProductionHouse", back_populates="contracts")
    renewed_from = relationship("ADPContract", remote_side=[contract_id])


# ============================================
# SCHEDULE (Phase 1)
# ============================================

class ADPSchedule(Base):
    __tablename__ = "adp_schedule"
    schedule_id = Column(BigInteger, primary_key=True)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    total_viewers = Column(BigInteger, nullable=False, default=0)
    tech_interrupt_yn = Column(CHAR(1), nullable=False, default='N')  # 'Y' or 'N'
    adp_episode_episode_id = Column(BigInteger, ForeignKey("adp_episode.episode_id"), nullable=False)
    
    episode = relationship("ADPEpisode", back_populates="schedules")


# ============================================
# FEEDBACK & WATCHLIST
# ============================================

class ADPFeedback(Base):
    __tablename__ = "adp_feedback"
    adp_account_account_id = Column(BigInteger, ForeignKey("adp_account.account_id"), primary_key=True)
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    feedback_text = Column(String(2000))
    rating = Column(SmallInteger, nullable=False)  # 1-5
    feedback_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    account = relationship("ADPAccount", back_populates="feedbacks")
    series = relationship("ADPSeries", back_populates="feedbacks")


class ADPWatchlist(Base):
    __tablename__ = "adp_watchlist"
    adp_account_account_id = Column(BigInteger, ForeignKey("adp_account.account_id"), primary_key=True)
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    added_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    account = relationship("ADPAccount", back_populates="watchlist_items")
    series = relationship("ADPSeries", back_populates="watchlist_entries")
