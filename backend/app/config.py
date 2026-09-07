from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AutoTrack API"
    environment: str = "development"
    shop_timezone: str = "UTC"
    currency: str = "USD"
    odometer_unit: str = "km"
    api_version: str = "0.1.0"

    model_config = SettingsConfigDict(
        env_prefix="AUTOTRACK_",
        env_file=("backend/.env", ".env"),
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
