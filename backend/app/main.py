from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import get_settings


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str


class ShopConfigResponse(BaseModel):
    timezone: str
    currency: str
    odometer_unit: str


class ApiError(BaseModel):
    code: str
    message: str
    details: list[dict[str, object]] | None = None


class ApiErrorResponse(BaseModel):
    error: ApiError


settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.api_version)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    del request
    return JSONResponse(
        status_code=422,
        content=ApiErrorResponse(
            error=ApiError(
                code="VALIDATION_ERROR",
                message="The request could not be processed.",
                details=[
                    {
                        "location": error["loc"],
                        "message": error["msg"],
                        "type": error["type"],
                    }
                    for error in exc.errors()
                ],
            )
        ).model_dump(),
    )


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


@app.get("/api/meta", tags=["system"])
def api_meta() -> dict[str, str]:
    return {
        "api_version": settings.api_version,
        "environment": settings.environment,
        "timestamp_policy": "UTC ISO 8601",
    }
