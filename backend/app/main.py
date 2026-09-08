import secrets
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from .auth import (
    STAFF_USERS,
    StaffUser,
    create_access_token,
    find_user,
    get_current_user,
    require_roles,
    verify_password,
)
from .config import get_settings
from .domain import StaffRole


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


class LoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


class StaffResponse(BaseModel):
    user_id: str
    email: str
    display_name: str
    role: StaffRole


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: StaffResponse


class AuditEventResponse(BaseModel):
    event_id: str
    event_type: str
    actor_user_id: str
    occurred_at: str


class AuditEventRequest(BaseModel):
    event_type: str = Field(min_length=1, max_length=80)


AUDIT_EVENTS: list[AuditEventResponse] = []


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


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    del request
    code = {
        401: "AUTHENTICATION_REQUIRED",
        403: "FORBIDDEN",
    }.get(exc.status_code, "REQUEST_FAILED")
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content=ApiErrorResponse(
            error=ApiError(code=code, message=str(exc.detail))
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


@app.post("/api/auth/login", response_model=LoginResponse, tags=["authentication"])
def login(request: LoginRequest) -> LoginResponse:
    user = find_user(str(request.email))
    if user is None or not verify_password(request.password, user):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")

    event = AuditEventResponse(
        event_id=secrets.token_hex(12),
        event_type="STAFF_LOGIN",
        actor_user_id=user.user_id,
        occurred_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    )
    AUDIT_EVENTS.append(event)
    return LoginResponse(
        access_token=create_access_token(user),
        user=StaffResponse.model_validate(user, from_attributes=True),
    )


@app.get("/api/auth/me", response_model=StaffResponse, tags=["authentication"])
def current_staff(
    user: Annotated[StaffUser, Depends(get_current_user)],
) -> StaffResponse:
    return StaffResponse.model_validate(user, from_attributes=True)


@app.get(
    "/api/admin/staff", response_model=list[StaffResponse], tags=["administration"]
)
def staff_directory(
    user: Annotated[StaffUser, Depends(require_roles(StaffRole.ADMIN_MANAGER))],
) -> list[StaffResponse]:
    del user
    return [
        StaffResponse.model_validate(staff, from_attributes=True)
        for staff in STAFF_USERS
    ]


@app.get("/api/audit/events", response_model=list[AuditEventResponse], tags=["audit"])
def audit_events(
    user: Annotated[StaffUser, Depends(get_current_user)],
) -> list[AuditEventResponse]:
    del user
    return AUDIT_EVENTS.copy()


@app.post("/api/admin/audit/events", response_model=AuditEventResponse, tags=["audit"])
def create_audit_event(
    request: AuditEventRequest,
    user: Annotated[StaffUser, Depends(require_roles(StaffRole.ADMIN_MANAGER))],
) -> AuditEventResponse:
    event = AuditEventResponse(
        event_id=secrets.token_hex(12),
        event_type=request.event_type,
        actor_user_id=user.user_id,
        occurred_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    )
    AUDIT_EVENTS.append(event)
    return event
