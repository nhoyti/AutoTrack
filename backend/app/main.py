from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AutoTrack API"
    environment: str = "development"
    shop_timezone: str = "UTC"
    currency: str = "USD"
    odometer_unit: str = "km"

    model_config = SettingsConfigDict(env_prefix="AUTOTRACK_", env_file=".env", extra="ignore")


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str


class ShopConfigResponse(BaseModel):
    timezone: str
    currency: str
    odometer_unit: str


settings = Settings()
app = FastAPI(title=settings.app_name, version="0.1.0")


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="autotrack-api",
        environment=settings.environment,
    )


@app.get("/api/config/shop", response_model=ShopConfigResponse, tags=["configuration"])
def shop_config() -> ShopConfigResponse:
    return ShopConfigResponse(
        timezone=settings.shop_timezone,
        currency=settings.currency,
        odometer_unit=settings.odometer_unit,
    )
