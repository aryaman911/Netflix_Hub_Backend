from datetime import datetime, date
from sqlalchemy import (
    Column, BigInteger, Integer, String, Boolean, Text, Date,
    ForeignKey, SmallInteger, Numeric, DateTime, UniqueConstraint
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
    country_code = Column(String, primary_key=True)
    country_name = Column(String, nullable=False)


class ADPLanguage(Base):
    __tablename__ = "adp_language"
    language_code = Column(String, primary_key=True)
    language_name = Column(String, nullable=False)


class ADPSeriesType(Base):
    __tablename__ = "adp_series_type"
    type_code = Column(String, primary_key=True)
    type_name = Column(String, nullable=False)


class ADPAccount(Base):
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
    
    user = relationship("ADPUser", back_populates="account")
    country = relationship("ADPCountry")
    feedbacks = relationship("ADPFeedback", back_populates="account")
    watchlist_items = relationship("ADPWatchlist", back_populates="account")


class ADPSeries(Base):
    __tablename__ = "adp_series"
    series_id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    num_episodes = Column(Integer, nullable=False, default=0)
    release_date = Column(Date, nullable=False)
    adp_language_language_code = Column(String, ForeignKey("adp_language.language_code"), nullable=False)
    origin_country = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    description = Column(Text)
    maturity_rating = Column(String)
    poster_url = Column(Text)
    banner_url = Column(Text)
    average_rating = Column(Numeric, nullable=False, default=0)
    rating_count = Column(Integer, nullable=False, default=0)
    
    language = relationship("ADPLanguage")
    genres = relationship("ADPSeriesGenre", back_populates="series")
    dubs = relationship("ADPSeriesDub", back_populates="series")
    subs = relationship("ADPSeriesSub", back_populates="series")
    feedbacks = relationship("ADPFeedback", back_populates="series")
    watchlist_entries = relationship("ADPWatchlist", back_populates="series")
    episodes = relationship("ADPEpisode", back_populates="series")


class ADPEpisode(Base):
    __tablename__ = "adp_episode"
    episode_id = Column(BigInteger, primary_key=True)
    episode_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), nullable=False)
    synopsis = Column(Text)
    runtime_minutes = Column(Integer)
    
    series = relationship("ADPSeries", back_populates="episodes")


class ADPSeriesGenre(Base):
    __tablename__ = "adp_series_genre"
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    adp_series_type_type_code = Column(String, ForeignKey("adp_series_type.type_code"), primary_key=True)
    series = relationship("ADPSeries", back_populates="genres")
    type = relationship("ADPSeriesType")


class ADPSeriesDub(Base):
    __tablename__ = "adp_series_dub"
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    adp_language_language_code = Column(String, ForeignKey("adp_language.language_code"), primary_key=True)
    series = relationship("ADPSeries", back_populates="dubs")
    language = relationship("ADPLanguage")


class ADPSeriesSub(Base):
    __tablename__ = "adp_series_sub"
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    adp_language_language_code = Column(String, ForeignKey("adp_language.language_code"), primary_key=True)
    series = relationship("ADPSeries", back_populates="subs")
    language = relationship("ADPLanguage")


class ADPFeedback(Base):
    __tablename__ = "adp_feedback"
    adp_account_account_id = Column(BigInteger, ForeignKey("adp_account.account_id"), primary_key=True)
    adp_series_series_id = Column(BigInteger, ForeignKey("adp_series.series_id"), primary_key=True)
    feedback_text = Column(String)
    rating = Column(SmallInteger, nullable=False)
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
