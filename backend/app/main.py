import hashlib
import hmac
import re
import secrets
import struct
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
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
from .domain import (
    ConcernSeverity,
    CustomerStatus,
    InspectionStatus,
    IntakeStatus,
    PreferredContactMethod,
    StaffRole,
)


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


@dataclass
class IntakeRecord:
    intake_id: str
    vehicle_id: str
    status: IntakeStatus = IntakeStatus.DRAFT
    notes: str | None = None
    created_at: str = field(default_factory=lambda: utc_now())
    updated_at: str = field(default_factory=lambda: utc_now())


@dataclass
class InspectionConcern:
    concern_id: str
    area: str
    condition: str
    severity: ConcernSeverity
    requested_work: str
    technician_notes: str | None = None
    recommendation: str | None = None


@dataclass
class InspectionRecord:
    inspection_id: str
    intake_id: str
    vehicle_id: str
    status: InspectionStatus = InspectionStatus.DRAFT
    concerns: list[InspectionConcern] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: utc_now())
    updated_at: str = field(default_factory=lambda: utc_now())


@dataclass
class PhotoRecord:
    photo_id: str
    inspection_id: str
    storage_key: str
    content: bytes
    mime_type: str
    file_name: str
    size_bytes: int
    width: int
    height: int
    created_at: str = field(default_factory=lambda: utc_now())


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


class IntakeCreateRequest(BaseModel):
    vehicle_id: str = Field(min_length=1)
    notes: str | None = Field(default=None, max_length=1000)


class IntakeUpdateRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=1000)


class IntakeResponse(BaseModel):
    intake_id: str
    vehicle_id: str
    status: IntakeStatus
    notes: str | None
    created_at: str
    updated_at: str


class ConcernRequest(BaseModel):
    area: str = Field(min_length=1, max_length=80)
    condition: str = Field(min_length=1, max_length=255)
    severity: ConcernSeverity
    requested_work: str = Field(min_length=1, max_length=500)
    technician_notes: str | None = Field(default=None, max_length=1000)
    recommendation: str | None = Field(default=None, max_length=1000)


class InspectionCreateRequest(BaseModel):
    intake_id: str = Field(min_length=1)
    concerns: list[ConcernRequest] = Field(default_factory=list, max_length=100)


class InspectionUpdateRequest(BaseModel):
    concerns: list[ConcernRequest] = Field(max_length=100)


class ConcernResponse(BaseModel):
    concern_id: str
    area: str
    condition: str
    severity: ConcernSeverity
    requested_work: str
    technician_notes: str | None
    recommendation: str | None


class InspectionResponse(BaseModel):
    inspection_id: str
    intake_id: str
    vehicle_id: str
    status: InspectionStatus
    concerns: list[ConcernResponse]
    created_at: str
    updated_at: str


class PhotoResponse(BaseModel):
    photo_id: str
    inspection_id: str
    storage_key: str
    file_name: str
    mime_type: str
    size_bytes: int
    width: int
    height: int
    url: str
    created_at: str


AUDIT_EVENTS: list[AuditEventResponse] = []
CUSTOMERS: list[CustomerRecord] = []
VEHICLES: list[VehicleRecord] = []
INTAKES: list[IntakeRecord] = []
INSPECTIONS: list[InspectionRecord] = []
PHOTOS: list[PhotoRecord] = []

PHOTO_MAX_BYTES = 10 * 1024 * 1024
PHOTO_MAX_DIMENSION = 10_000
PHOTO_URL_TTL_SECONDS = 300


def image_dimensions(content: bytes, mime_type: str) -> tuple[int, int]:
    if mime_type == "image/png" and content.startswith(b"\x89PNG\r\n\x1a\n"):
        width, height = struct.unpack(">II", content[16:24])
        return width, height
    if mime_type == "image/gif" and content[:6] in (b"GIF87a", b"GIF89a"):
        width, height = struct.unpack("<HH", content[6:10])
        return width, height
    if mime_type == "image/jpeg" and content[:2] == b"\xff\xd8":
        offset = 2
        while offset + 9 < len(content):
            if content[offset] != 0xFF:
                offset += 1
                continue
            marker = content[offset + 1]
            offset += 2
            if marker in (0xD8, 0xD9):
                continue
            segment_length = struct.unpack(">H", content[offset : offset + 2])[0]
            if marker in range(0xC0, 0xC4):
                height, width = struct.unpack(">HH", content[offset + 3 : offset + 7])
                return width, height
            offset += segment_length
    raise HTTPException(
        status_code=400,
        detail="PHOTO_INVALID: The uploaded file is not a supported image.",
    )


def get_intake_or_404(intake_id: str) -> IntakeRecord:
    intake = next((item for item in INTAKES if item.intake_id == intake_id), None)
    if intake is None:
        raise HTTPException(status_code=404, detail="Intake was not found.")
    return intake


def get_inspection_or_404(inspection_id: str) -> InspectionRecord:
    inspection = next(
        (item for item in INSPECTIONS if item.inspection_id == inspection_id), None
    )
    if inspection is None:
        raise HTTPException(status_code=404, detail="Inspection was not found.")
    return inspection


def signed_photo_token(photo_id: str, expires_at: int) -> str:
    payload = f"{photo_id}.{expires_at}"
    signature = hmac.new(
        settings.auth_secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return f"{payload}.{signature}"


def verify_photo_token(photo_id: str, token: str) -> None:
    try:
        token_photo_id, expires_at, signature = token.split(".", 2)
        payload = f"{token_photo_id}.{expires_at}"
        expected = hmac.new(
            settings.auth_secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        if (
            token_photo_id != photo_id
            or not hmac.compare_digest(signature, expected)
            or int(expires_at) < int(datetime.now(UTC).timestamp())
        ):
            raise ValueError
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=403, detail="The photo URL is invalid or expired."
        ) from None


def photo_response(photo: PhotoRecord) -> PhotoResponse:
    expires_at = int(datetime.now(UTC).timestamp()) + PHOTO_URL_TTL_SECONDS
    return PhotoResponse(
        photo_id=photo.photo_id,
        inspection_id=photo.inspection_id,
        storage_key=photo.storage_key,
        file_name=photo.file_name,
        mime_type=photo.mime_type,
        size_bytes=photo.size_bytes,
        width=photo.width,
        height=photo.height,
        url=(
            f"/api/photos/{photo.photo_id}/content?token="
            f"{signed_photo_token(photo.photo_id, expires_at)}"
        ),
        created_at=photo.created_at,
    )


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


def intake_response(intake: IntakeRecord) -> IntakeResponse:
    return IntakeResponse.model_validate(intake, from_attributes=True)


def concern_from_request(request: ConcernRequest) -> InspectionConcern:
    return InspectionConcern(
        concern_id=uuid4().hex,
        area=request.area.strip(),
        condition=request.condition.strip(),
        severity=request.severity,
        requested_work=request.requested_work.strip(),
        technician_notes=(
            request.technician_notes.strip() if request.technician_notes else None
        ),
        recommendation=(
            request.recommendation.strip() if request.recommendation else None
        ),
    )


@app.post(
    "/api/intakes",
    response_model=IntakeResponse,
    status_code=201,
    tags=["intake"],
)
def create_or_resume_intake(
    request: IntakeCreateRequest,
    user: Annotated[
        StaffUser,
        Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR)),
    ],
) -> IntakeResponse:
    del user
    get_vehicle_or_404(request.vehicle_id)
    existing = next(
        (
            intake
            for intake in INTAKES
            if intake.vehicle_id == request.vehicle_id
            and intake.status == IntakeStatus.DRAFT
        ),
        None,
    )
    if existing is not None:
        if request.notes is not None:
            existing.notes = request.notes.strip() or None
            existing.updated_at = utc_now()
        return intake_response(existing)

    intake = IntakeRecord(
        intake_id=uuid4().hex,
        vehicle_id=request.vehicle_id,
        notes=request.notes.strip() if request.notes else None,
    )
    INTAKES.append(intake)
    return intake_response(intake)


@app.get("/api/intakes/{intake_id}", response_model=IntakeResponse, tags=["intake"])
def get_intake(
    intake_id: str,
    user: Annotated[StaffUser, Depends(get_current_user)],
) -> IntakeResponse:
    del user
    return intake_response(get_intake_or_404(intake_id))


@app.patch("/api/intakes/{intake_id}", response_model=IntakeResponse, tags=["intake"])
def update_intake(
    intake_id: str,
    request: IntakeUpdateRequest,
    user: Annotated[
        StaffUser,
        Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR)),
    ],
) -> IntakeResponse:
    del user
    intake = get_intake_or_404(intake_id)
    if intake.status == IntakeStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="A completed intake is immutable.")
    intake.notes = request.notes.strip() if request.notes else None
    intake.updated_at = utc_now()
    return intake_response(intake)


@app.post(
    "/api/intakes/{intake_id}/complete",
    response_model=IntakeResponse,
    tags=["intake"],
)
def complete_intake(
    intake_id: str,
    user: Annotated[
        StaffUser,
        Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR)),
    ],
) -> IntakeResponse:
    del user
    intake = get_intake_or_404(intake_id)
    intake.status = IntakeStatus.COMPLETED
    intake.updated_at = utc_now()
    return intake_response(intake)


def inspection_response(inspection: InspectionRecord) -> InspectionResponse:
    return InspectionResponse.model_validate(inspection, from_attributes=True)


@app.post(
    "/api/inspections",
    response_model=InspectionResponse,
    status_code=201,
    tags=["inspections"],
)
def create_inspection(
    request: InspectionCreateRequest,
    user: Annotated[
        StaffUser,
        Depends(
            require_roles(
                StaffRole.ADMIN_MANAGER,
                StaffRole.SERVICE_ADVISOR,
                StaffRole.TECHNICIAN_PAINTER,
            )
        ),
    ],
) -> InspectionResponse:
    del user
    intake = get_intake_or_404(request.intake_id)
    existing = next(
        (item for item in INSPECTIONS if item.intake_id == intake.intake_id), None
    )
    if existing is not None:
        return inspection_response(existing)
    inspection = InspectionRecord(
        inspection_id=uuid4().hex,
        intake_id=intake.intake_id,
        vehicle_id=intake.vehicle_id,
        concerns=[concern_from_request(item) for item in request.concerns],
    )
    INSPECTIONS.append(inspection)
    return inspection_response(inspection)


@app.get(
    "/api/inspections/{inspection_id}",
    response_model=InspectionResponse,
    tags=["inspections"],
)
def get_inspection(
    inspection_id: str,
    user: Annotated[StaffUser, Depends(get_current_user)],
) -> InspectionResponse:
    del user
    return inspection_response(get_inspection_or_404(inspection_id))


@app.patch(
    "/api/inspections/{inspection_id}",
    response_model=InspectionResponse,
    tags=["inspections"],
)
def update_inspection(
    inspection_id: str,
    request: InspectionUpdateRequest,
    user: Annotated[
        StaffUser,
        Depends(
            require_roles(
                StaffRole.ADMIN_MANAGER,
                StaffRole.SERVICE_ADVISOR,
                StaffRole.TECHNICIAN_PAINTER,
            )
        ),
    ],
) -> InspectionResponse:
    del user
    inspection = get_inspection_or_404(inspection_id)
    if inspection.status == InspectionStatus.COMPLETED:
        raise HTTPException(
            status_code=409, detail="A completed inspection is immutable."
        )
    inspection.concerns = [concern_from_request(item) for item in request.concerns]
    inspection.updated_at = utc_now()
    return inspection_response(inspection)


@app.post(
    "/api/inspections/{inspection_id}/complete",
    response_model=InspectionResponse,
    tags=["inspections"],
)
def complete_inspection(
    inspection_id: str,
    user: Annotated[
        StaffUser,
        Depends(
            require_roles(
                StaffRole.ADMIN_MANAGER,
                StaffRole.SERVICE_ADVISOR,
                StaffRole.TECHNICIAN_PAINTER,
            )
        ),
    ],
) -> InspectionResponse:
    del user
    inspection = get_inspection_or_404(inspection_id)
    if not inspection.concerns:
        raise HTTPException(
            status_code=400, detail="An inspection must contain at least one concern."
        )
    inspection.status = InspectionStatus.COMPLETED
    inspection.updated_at = utc_now()
    return inspection_response(inspection)


@app.post(
    "/api/inspections/{inspection_id}/photos",
    response_model=PhotoResponse,
    status_code=201,
    tags=["photos"],
)
def upload_inspection_photo(
    inspection_id: str,
    file: Annotated[UploadFile, File(...)],
    user: Annotated[
        StaffUser,
        Depends(
            require_roles(
                StaffRole.ADMIN_MANAGER,
                StaffRole.SERVICE_ADVISOR,
                StaffRole.TECHNICIAN_PAINTER,
            )
        ),
    ],
) -> PhotoResponse:
    del user
    inspection = get_inspection_or_404(inspection_id)
    allowed_types = {"image/jpeg", "image/png", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=(
                "PHOTO_MIME_UNSUPPORTED: Only JPEG, PNG, and GIF images are allowed."
            ),
        )
    content = file.file.read(PHOTO_MAX_BYTES + 1)
    if len(content) > PHOTO_MAX_BYTES:
        raise HTTPException(
            status_code=413, detail="PHOTO_TOO_LARGE: The image exceeds 10 MB."
        )
    width, height = image_dimensions(content, file.content_type)
    if width < 1 or height < 1 or max(width, height) > PHOTO_MAX_DIMENSION:
        raise HTTPException(
            status_code=400,
            detail="PHOTO_DIMENSIONS_INVALID: The image dimensions are not supported.",
        )
    photo = PhotoRecord(
        photo_id=uuid4().hex,
        inspection_id=inspection.inspection_id,
        storage_key=f"inspections/{inspection.inspection_id}/{uuid4().hex}",
        content=content,
        mime_type=file.content_type,
        file_name=file.filename or "inspection-photo",
        size_bytes=len(content),
        width=width,
        height=height,
    )
    PHOTOS.append(photo)
    return photo_response(photo)


@app.get("/api/photos/{photo_id}", response_model=PhotoResponse, tags=["photos"])
def get_photo(
    photo_id: str,
    user: Annotated[StaffUser, Depends(get_current_user)],
) -> PhotoResponse:
    del user
    photo = next((item for item in PHOTOS if item.photo_id == photo_id), None)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo was not found.")
    return photo_response(photo)


@app.get("/api/photos/{photo_id}/content", tags=["photos"])
def get_photo_content(photo_id: str, token: str = Query(...)) -> Response:
    verify_photo_token(photo_id, token)
    photo = next((item for item in PHOTOS if item.photo_id == photo_id), None)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo was not found.")
    return Response(content=photo.content, media_type=photo.mime_type)
