import re
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request
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
from .domain import CustomerStatus, PreferredContactMethod, StaffRole


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


@dataclass
class CustomerRecord:
    customer_id: str
    full_name: str
    mobile_number: str | None = None
    email: str | None = None
    address: str | None = None
    preferred_contact_method: PreferredContactMethod = PreferredContactMethod.SMS
    notes: str | None = None
    status: CustomerStatus = CustomerStatus.ACTIVE
    created_at: str = field(default_factory=lambda: utc_now())
    updated_at: str = field(default_factory=lambda: utc_now())


@dataclass
class OdometerReading:
    reading_id: str
    value: int
    unit: str
    recorded_at: str
    source_record: str
    actor_user_id: str | None = None
    is_correction: bool = False
    reason: str | None = None


@dataclass
class VehicleRecord:
    vehicle_id: str
    customer_id: str
    plate_number: str
    vin_chassis_number: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    color: str | None = None
    fuel_type: str | None = None
    transmission: str | None = None
    current_odometer: int = 0
    notes: str | None = None
    created_at: str = field(default_factory=lambda: utc_now())
    updated_at: str = field(default_factory=lambda: utc_now())
    odometer_readings: list[OdometerReading] = field(default_factory=list)


class CustomerCreateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    mobile_number: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=120)
    address: str | None = Field(default=None, max_length=255)
    preferred_contact_method: PreferredContactMethod = PreferredContactMethod.SMS
    notes: str | None = Field(default=None, max_length=500)
    status: CustomerStatus = CustomerStatus.ACTIVE


class CustomerUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    mobile_number: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=120)
    address: str | None = Field(default=None, max_length=255)
    preferred_contact_method: PreferredContactMethod | None = None
    notes: str | None = Field(default=None, max_length=500)
    status: CustomerStatus | None = None


class CustomerResponse(BaseModel):
    customer_id: str
    full_name: str
    mobile_number: str | None = None
    email: str | None = None
    address: str | None = None
    preferred_contact_method: PreferredContactMethod
    notes: str | None = None
    status: CustomerStatus
    created_at: str
    updated_at: str


class VehicleCreateRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    plate_number: str = Field(min_length=1, max_length=40)
    vin_chassis_number: str | None = Field(default=None, max_length=60)
    make: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=80)
    year: int | None = Field(default=None, ge=1900, le=2100)
    color: str | None = Field(default=None, max_length=60)
    fuel_type: str | None = Field(default=None, max_length=40)
    transmission: str | None = Field(default=None, max_length=40)
    current_odometer: int = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=500)


class VehicleUpdateRequest(BaseModel):
    customer_id: str | None = Field(default=None, min_length=1)
    plate_number: str | None = Field(default=None, min_length=1, max_length=40)
    vin_chassis_number: str | None = Field(default=None, max_length=60)
    make: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=80)
    year: int | None = Field(default=None, ge=1900, le=2100)
    color: str | None = Field(default=None, max_length=60)
    fuel_type: str | None = Field(default=None, max_length=40)
    transmission: str | None = Field(default=None, max_length=40)
    notes: str | None = Field(default=None, max_length=500)


class OdometerReadingRequest(BaseModel):
    value: int = Field(ge=0)
    source_record: str = Field(min_length=1, max_length=80)


class OdometerCorrectionRequest(BaseModel):
    previous_value: int = Field(ge=0)
    corrected_value: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=255)
    actor_user_id: str = Field(min_length=1, max_length=80)


class OdometerReadingResponse(BaseModel):
    reading_id: str
    value: int
    unit: str
    recorded_at: str
    source_record: str
    actor_user_id: str | None = None
    is_correction: bool = False
    reason: str | None = None


class VehicleResponse(BaseModel):
    vehicle_id: str
    customer_id: str
    plate_number: str
    vin_chassis_number: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    color: str | None = None
    fuel_type: str | None = None
    transmission: str | None = None
    current_odometer: int
    notes: str | None = None
    created_at: str
    updated_at: str
    odometer_readings: list[OdometerReadingResponse]


class OdometerCorrectionResponse(BaseModel):
    vehicle_id: str
    current_odometer: int
    readings: list[OdometerReadingResponse]


AUDIT_EVENTS: list[AuditEventResponse] = []
CUSTOMERS: list[CustomerRecord] = []
VEHICLES: list[VehicleRecord] = []


settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.api_version)


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def normalize_search_value(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "", value.strip().lower())


def get_customer_or_404(customer_id: str) -> CustomerRecord:
    customer = next(
        (item for item in CUSTOMERS if item.customer_id == customer_id),
        None,
    )
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer was not found.")
    return customer


def get_vehicle_or_404(vehicle_id: str) -> VehicleRecord:
    vehicle = next(
        (item for item in VEHICLES if item.vehicle_id == vehicle_id),
        None,
    )
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle was not found.")
    return vehicle


def record_odometer_reading(
    vehicle: VehicleRecord,
    value: int,
    source_record: str,
    *,
    actor_user_id: str | None = None,
    is_correction: bool = False,
    reason: str | None = None,
) -> None:
    if value < vehicle.current_odometer and not is_correction:
        raise HTTPException(
            status_code=400,
            detail=(
                "ODOMETER_REGRESSION: The odometer reading cannot be lower "
                "than the latest accepted value."
            ),
        )

    reading = OdometerReading(
        reading_id=uuid4().hex,
        value=value,
        unit=settings.odometer_unit,
        recorded_at=utc_now(),
        source_record=source_record,
        actor_user_id=actor_user_id,
        is_correction=is_correction,
        reason=reason,
    )
    vehicle.odometer_readings.append(reading)
    vehicle.current_odometer = value
    vehicle.updated_at = utc_now()


def customer_matches_search(customer: CustomerRecord, query: str) -> bool:
    if not query:
        return True
    needle = normalize_search_value(query)
    return any(
        normalize_search_value(value) and needle in normalize_search_value(value)
        for value in (
            customer.full_name,
            customer.mobile_number,
            customer.email,
        )
        if value is not None
    )


def vehicle_matches_search(vehicle: VehicleRecord, query: str) -> bool:
    if not query:
        return True
    needle = normalize_search_value(query)
    haystacks = [
        vehicle.plate_number,
        vehicle.vin_chassis_number,
        vehicle.make,
        vehicle.model,
        vehicle.color,
    ]
    return any(
        normalize_search_value(value) and needle in normalize_search_value(value)
        for value in haystacks
        if value
    )


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
    detail = str(exc.detail)
    code = {
        401: "AUTHENTICATION_REQUIRED",
        403: "FORBIDDEN",
    }.get(exc.status_code, "REQUEST_FAILED")
    if detail.startswith("ODOMETER_REGRESSION:"):
        code = "ODOMETER_REGRESSION"
        detail = detail.split(": ", 1)[1]
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content=ApiErrorResponse(
            error=ApiError(code=code, message=detail)
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
        occurred_at=utc_now(),
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
        occurred_at=utc_now(),
    )
    AUDIT_EVENTS.append(event)
    return event


@app.post(
    "/api/customers",
    response_model=CustomerResponse,
    status_code=201,
    tags=["customers"],
)
def create_customer(
    request: CustomerCreateRequest,
    user: Annotated[
        StaffUser,
        Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR)),
    ],
) -> CustomerResponse:
    del user

    if request.email is not None:
        normalized_email = request.email.strip().lower()
        if any(
            customer.email is not None
            and customer.email.strip().lower() == normalized_email
            for customer in CUSTOMERS
        ):
            raise HTTPException(
                status_code=409,
                detail="A customer with that email already exists.",
            )

    customer = CustomerRecord(
        customer_id=uuid4().hex,
        full_name=request.full_name.strip(),
        mobile_number=request.mobile_number.strip() if request.mobile_number else None,
        email=request.email.strip() if request.email else None,
        address=request.address.strip() if request.address else None,
        preferred_contact_method=request.preferred_contact_method,
        notes=request.notes.strip() if request.notes else None,
        status=request.status,
    )
    CUSTOMERS.append(customer)
    return CustomerResponse.model_validate(customer, from_attributes=True)


@app.get("/api/customers", response_model=list[CustomerResponse], tags=["customers"])
def list_customers(
    search: Annotated[str | None, Query()] = None,
    user: Annotated[StaffUser, Depends(get_current_user)] = None,
) -> list[CustomerResponse]:
    del user
    query = (search or "").strip()
    return [
        CustomerResponse.model_validate(customer, from_attributes=True)
        for customer in CUSTOMERS
        if customer_matches_search(customer, query)
    ]


@app.get(
    "/api/customers/{customer_id}",
    response_model=CustomerResponse,
    tags=["customers"],
)
def get_customer(
    customer_id: str,
    user: Annotated[StaffUser, Depends(get_current_user)],
) -> CustomerResponse:
    del user
    return CustomerResponse.model_validate(
        get_customer_or_404(customer_id),
        from_attributes=True,
    )


@app.patch(
    "/api/customers/{customer_id}",
    response_model=CustomerResponse,
    tags=["customers"],
)
def update_customer(
    customer_id: str,
    request: CustomerUpdateRequest,
    user: Annotated[
        StaffUser,
        Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR)),
    ],
) -> CustomerResponse:
    del user
    customer = get_customer_or_404(customer_id)

    if request.full_name is not None:
        customer.full_name = request.full_name.strip()
    if request.mobile_number is not None:
        customer.mobile_number = request.mobile_number.strip() or None
    if request.email is not None:
        normalized_email = request.email.strip().lower()
        if any(
            item.customer_id != customer.customer_id
            and item.email is not None
            and item.email.strip().lower() == normalized_email
            for item in CUSTOMERS
        ):
            raise HTTPException(
                status_code=409,
                detail="A customer with that email already exists.",
            )
        customer.email = normalized_email or None
    if request.address is not None:
        customer.address = request.address.strip() or None
    if request.preferred_contact_method is not None:
        customer.preferred_contact_method = request.preferred_contact_method
    if request.notes is not None:
        customer.notes = request.notes.strip() or None
    if request.status is not None:
        customer.status = request.status
    customer.updated_at = utc_now()
    return CustomerResponse.model_validate(customer, from_attributes=True)


@app.post(
    "/api/vehicles",
    response_model=VehicleResponse,
    status_code=201,
    tags=["vehicles"],
)
def create_vehicle(
    request: VehicleCreateRequest,
    user: Annotated[
        StaffUser,
        Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR)),
    ],
) -> VehicleResponse:
    get_customer_or_404(request.customer_id)

    normalized_plate = request.plate_number.strip()
    if any(
        item.plate_number.strip().lower() == normalized_plate.lower()
        for item in VEHICLES
    ):
        raise HTTPException(
            status_code=409,
            detail="A vehicle with that plate number already exists.",
        )

    if request.vin_chassis_number is not None:
        normalized_vin = request.vin_chassis_number.strip().upper()
        if any(
            item.vin_chassis_number is not None
            and item.vin_chassis_number.strip().upper() == normalized_vin
            for item in VEHICLES
        ):
            raise HTTPException(
                status_code=409,
                detail="A vehicle with that VIN/chassis number already exists.",
            )

    vehicle = VehicleRecord(
        vehicle_id=uuid4().hex,
        customer_id=request.customer_id,
        plate_number=normalized_plate,
        vin_chassis_number=(
            request.vin_chassis_number.strip().upper()
            if request.vin_chassis_number
            else None
        ),
        make=request.make.strip() if request.make else None,
        model=request.model.strip() if request.model else None,
        year=request.year,
        color=request.color.strip() if request.color else None,
        fuel_type=request.fuel_type.strip() if request.fuel_type else None,
        transmission=request.transmission.strip() if request.transmission else None,
        current_odometer=request.current_odometer,
        notes=request.notes.strip() if request.notes else None,
    )
    if request.current_odometer > 0:
        vehicle.odometer_readings.append(
            OdometerReading(
                reading_id=uuid4().hex,
                value=request.current_odometer,
                unit=settings.odometer_unit,
                recorded_at=utc_now(),
                source_record="INITIAL_INTAKE",
                actor_user_id=user.user_id,
            )
        )
    VEHICLES.append(vehicle)
    return VehicleResponse.model_validate(vehicle, from_attributes=True)


@app.get("/api/vehicles", response_model=list[VehicleResponse], tags=["vehicles"])
def list_vehicles(
    search: Annotated[str | None, Query()] = None,
    user: Annotated[StaffUser, Depends(get_current_user)] = None,
) -> list[VehicleResponse]:
    del user
    query = (search or "").strip()
    return [
        VehicleResponse.model_validate(vehicle, from_attributes=True)
        for vehicle in VEHICLES
        if vehicle_matches_search(vehicle, query)
    ]


@app.get(
    "/api/vehicles/{vehicle_id}",
    response_model=VehicleResponse,
    tags=["vehicles"],
)
def get_vehicle(
    vehicle_id: str,
    user: Annotated[StaffUser, Depends(get_current_user)],
) -> VehicleResponse:
    del user
    return VehicleResponse.model_validate(
        get_vehicle_or_404(vehicle_id),
        from_attributes=True,
    )


@app.patch(
    "/api/vehicles/{vehicle_id}",
    response_model=VehicleResponse,
    tags=["vehicles"],
)
def update_vehicle(
    vehicle_id: str,
    request: VehicleUpdateRequest,
    user: Annotated[
        StaffUser,
        Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR)),
    ],
) -> VehicleResponse:
    del user
    vehicle = get_vehicle_or_404(vehicle_id)

    if request.customer_id is not None:
        get_customer_or_404(request.customer_id)
        vehicle.customer_id = request.customer_id
    if request.plate_number is not None:
        normalized_plate = request.plate_number.strip()
        if any(
            item.vehicle_id != vehicle.vehicle_id
            and item.plate_number.strip().lower() == normalized_plate.lower()
            for item in VEHICLES
        ):
            raise HTTPException(
                status_code=409,
                detail="A vehicle with that plate number already exists.",
            )
        vehicle.plate_number = normalized_plate
    if request.vin_chassis_number is not None:
        normalized_vin = request.vin_chassis_number.strip().upper() or None
        if normalized_vin is not None and any(
            item.vehicle_id != vehicle.vehicle_id
            and item.vin_chassis_number is not None
            and item.vin_chassis_number.strip().upper() == normalized_vin
            for item in VEHICLES
        ):
            raise HTTPException(
                status_code=409,
                detail="A vehicle with that VIN/chassis number already exists.",
            )
        vehicle.vin_chassis_number = normalized_vin
    if request.make is not None:
        vehicle.make = request.make.strip() or None
    if request.model is not None:
        vehicle.model = request.model.strip() or None
    if request.year is not None:
        vehicle.year = request.year
    if request.color is not None:
        vehicle.color = request.color.strip() or None
    if request.fuel_type is not None:
        vehicle.fuel_type = request.fuel_type.strip() or None
    if request.transmission is not None:
        vehicle.transmission = request.transmission.strip() or None
    if request.notes is not None:
        vehicle.notes = request.notes.strip() or None

    vehicle.updated_at = utc_now()
    return VehicleResponse.model_validate(vehicle, from_attributes=True)


@app.post(
    "/api/vehicles/{vehicle_id}/odometer/readings",
    response_model=OdometerCorrectionResponse,
    tags=["vehicles"],
)
def add_odometer_reading(
    vehicle_id: str,
    request: OdometerReadingRequest,
    user: Annotated[
        StaffUser,
        Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR)),
    ],
) -> OdometerCorrectionResponse:
    vehicle = get_vehicle_or_404(vehicle_id)
    try:
        record_odometer_reading(
            vehicle,
            request.value,
            request.source_record,
            actor_user_id=user.user_id,
        )
    except HTTPException as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc.detail),
        ) from None

    return OdometerCorrectionResponse(
        vehicle_id=vehicle.vehicle_id,
        current_odometer=vehicle.current_odometer,
        readings=[
            OdometerReadingResponse.model_validate(reading, from_attributes=True)
            for reading in vehicle.odometer_readings
        ],
    )


@app.post(
    "/api/vehicles/{vehicle_id}/odometer/corrections",
    response_model=OdometerCorrectionResponse,
    status_code=201,
    tags=["vehicles"],
)
def create_odometer_correction(
    vehicle_id: str,
    request: OdometerCorrectionRequest,
    user: Annotated[
        StaffUser,
        Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR)),
    ],
) -> OdometerCorrectionResponse:
    vehicle = get_vehicle_or_404(vehicle_id)
    if request.corrected_value < request.previous_value:
        raise HTTPException(
            status_code=400,
            detail=(
                "The corrected odometer value must be greater than or equal "
                "to the previous value."
            ),
        )

    record_odometer_reading(
        vehicle,
        request.corrected_value,
        "ODOMETER_CORRECTION",
        actor_user_id=request.actor_user_id,
        is_correction=True,
        reason=request.reason,
    )

    return OdometerCorrectionResponse(
        vehicle_id=vehicle.vehicle_id,
        current_odometer=vehicle.current_odometer,
        readings=[
            OdometerReadingResponse.model_validate(reading, from_attributes=True)
            for reading in vehicle.odometer_readings
        ],
    )
