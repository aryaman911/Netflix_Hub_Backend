from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Supabase / Postgres connection string, e.g.
    # postgres://user:password@host:5432/postgres
    DATABASE_URL: str

    # JWT settings
    JWT_SECRET_KEY: str = "super-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()