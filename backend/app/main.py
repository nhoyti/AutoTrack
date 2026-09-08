from __future__ import annotations

import base64
import hashlib
import io
import re
import uuid
from copy import deepcopy
from datetime import UTC, date, datetime
from typing import Any, Literal

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse, Response
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field

from app.auth import (
    STAFF_USERS,
    StaffUser,
    create_access_token,
    find_user,
    get_current_user,
    require_roles,
    verify_password,
)
from app.config import get_settings
from app.domain import (
    ConcernSeverity,
    InspectionStatus,
    IntakeStatus,
    JobStatus,
    ScheduleRuleType,
    ScheduleStatus,
    ServiceStatus,
    StaffRole,
)

settings = get_settings()


class ApiErrorDetail(BaseModel):
    code: str
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str


class ShopConfigResponse(BaseModel):
    timezone: str
    currency: str
    odometer_unit: str


class ApiMetaResponse(BaseModel):
    api_version: str
    environment: str
    timestamp_policy: str


class LoginRequest(BaseModel):
    email: str
    password: str


class CustomerCreateRequest(BaseModel):
    full_name: str
    mobile_number: str | None = None
    email: str | None = None
    preferred_contact_method: str | None = None
    status: str = "ACTIVE"


class VehicleCreateRequest(BaseModel):
    customer_id: str
    plate_number: str
    vin_chassis_number: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    color: str | None = None
    current_odometer: int | None = None


class VehiclePatchRequest(BaseModel):
    plate_number: str | None = None
    color: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    vin_chassis_number: str | None = None


class OdometerReadingRequest(BaseModel):
    value: int
    source_record: str


class OdometerCorrectionRequest(BaseModel):
    previous_value: int
    corrected_value: int
    reason: str
    actor_user_id: str


class IntakeCreateRequest(BaseModel):
    vehicle_id: str
    notes: str | None = None


class InspectionConcern(BaseModel):
    area: str | None = None
    condition: str | None = None
    severity: str | None = None
    requested_work: str | None = None
    technician_notes: str | None = None
    recommendation: str | None = None

    model_config = ConfigDict(extra="allow")


class InspectionCreateRequest(BaseModel):
    intake_id: str
    concerns: list[InspectionConcern] = Field(default_factory=list)
    customer_notes: str | None = None
    technician_notes: str | None = None
    overall_condition: str | None = None


class JobCreateRequest(BaseModel):
    inspection_id: str
    vehicle_id: str | None = None
    job_type: str = "PAINT_BODY"
    description: str | None = None
    estimated_cost: float | None = None
    customer_notes: str | None = None
    technician_notes: str | None = None


class JobStatusRequest(BaseModel):
    status: str
    reason: str | None = None


class ServiceItemRequest(BaseModel):
    service_category: str
    description: str
    status: str = "COMPLETED"
    cost: float = Field(default=0, ge=0)
    next_due_odometer: int | None = Field(default=None, ge=0)
    next_due_date: date | None = None
    rule_type: str | None = None
    maintenance_type: str | None = None


class ServicePartRequest(BaseModel):
    part_name: str
    part_number: str | None = None
    quantity: float = Field(default=1, gt=0)
    unit_cost: float = Field(default=0, ge=0)


class ServiceRecordRequest(BaseModel):
    vehicle_id: str
    service_date: date
    service_type: str
    description: str | None = None
    odometer_reading: int | None = Field(default=None, ge=0)
    labor_cost: float = Field(default=0, ge=0)
    parts_cost: float | None = Field(default=None, ge=0)
    recommendations: str | None = None
    items: list[ServiceItemRequest] = Field(default_factory=list)
    parts: list[ServicePartRequest] = Field(default_factory=list)


class ServiceCancelRequest(BaseModel):
    reason: str | None = None


class ScheduleEvaluationRequest(BaseModel):
    evaluated_at: datetime | None = None
    odometer: int | None = Field(default=None, ge=0)


def utc_now() -> datetime:
    return datetime.now(UTC)


def iso_utc(value: datetime | None = None) -> str:
    ts = value or utc_now()
    return ts.astimezone(UTC).isoformat().replace("+00:00", "Z")


def raise_api_error(code: str, message: str, status_code: int) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


async def http_exception_handler(_: Any, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "ERROR", "message": str(exc.detail)}
    if detail.get("code") in {"AUTHENTICATION_REQUIRED", "FORBIDDEN", "VALIDATION_ERROR"}:
        payload = {"error": detail}
    else:
        payload = {"error": detail}
    return JSONResponse(status_code=exc.status_code, content=payload)


app = FastAPI(title=settings.app_name, version=settings.api_version)
app.add_exception_handler(HTTPException, http_exception_handler)

CUSTOMERS: dict[str, dict[str, Any]] = {}
VEHICLES: dict[str, dict[str, Any]] = {}
INTAKES: dict[str, dict[str, Any]] = {}
INSPECTIONS: dict[str, dict[str, Any]] = {}
JOBS: dict[str, dict[str, Any]] = {}
SERVICES: dict[str, dict[str, Any]] = {}
MAINTENANCE_SCHEDULES: dict[str, dict[str, Any]] = {}
AUDIT_EVENTS: list[dict[str, Any]] = []
SIGNED_PHOTOS: dict[str, dict[str, Any]] = {}


def record_audit(event_type: str, actor_user_id: str | None = None, details: dict[str, Any] | None = None) -> None:
    AUDIT_EVENTS.append(
        {
            "event_id": uuid.uuid4().hex,
            "event_type": event_type,
            "actor_user_id": actor_user_id,
            "details": details or {},
            "occurred_at": iso_utc(),
        }
    )


def get_vehicle_or_404(vehicle_id: str) -> dict[str, Any]:
    vehicle = VEHICLES.get(vehicle_id)
    if vehicle is None:
        raise_api_error("VEHICLE_NOT_FOUND", "Vehicle not found.", status.HTTP_404_NOT_FOUND)
    return vehicle


def get_inspection_or_404(inspection_id: str) -> dict[str, Any]:
    inspection = INSPECTIONS.get(inspection_id)
    if inspection is None:
        raise_api_error("INSPECTION_NOT_FOUND", "Inspection not found.", status.HTTP_404_NOT_FOUND)
    return inspection


def get_job_or_404(job_id: str) -> dict[str, Any]:
    job = JOBS.get(job_id)
    if job is None:
        raise_api_error("JOB_NOT_FOUND", "Job not found.", status.HTTP_404_NOT_FOUND)
    return job


def sanitize_user_payload(user: StaffUser) -> dict[str, Any]:
    return {
        "user_id": user.user_id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role.value,
    }


def normalize_plate(value: str) -> str:
    return re.sub(r"\s+", "", value or "").upper()


def allowed_transition(user: StaffUser, current: str, target: str) -> bool:
    current = current or "DRAFT"
    target = target.upper()
    if current == "COMPLETED" or current == "CANCELLED":
        return False
    if target == "CANCELLED":
        return user.role in {StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR, StaffRole.TECHNICIAN_PAINTER}
    allowed = {
        "DRAFT": {"INSPECTION", "CANCELLED"},
        "INSPECTION": {"ESTIMATE"},
        "ESTIMATE": {"CUSTOMER_APPROVAL"},
        "CUSTOMER_APPROVAL": {"SCHEDULED"},
        "SCHEDULED": {"IN_PROGRESS"},
        "IN_PROGRESS": {"QUALITY_CHECK"},
        "QUALITY_CHECK": {"READY_FOR_RELEASE"},
        "READY_FOR_RELEASE": {"COMPLETED"},
    }
    if target not in allowed.get(current, set()):
        return False
    if target in {"ESTIMATE", "CUSTOMER_APPROVAL", "SCHEDULED"}:
        return user.role in {StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR}
    if target in {"IN_PROGRESS", "QUALITY_CHECK", "READY_FOR_RELEASE", "COMPLETED"}:
        return user.role in {StaffRole.ADMIN_MANAGER, StaffRole.TECHNICIAN_PAINTER}
    return user.role in {StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR, StaffRole.TECHNICIAN_PAINTER}


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="autotrack-api",
        environment=settings.environment,
    )


@app.get("/api/meta", response_model=ApiMetaResponse, tags=["system"])
def api_meta() -> ApiMetaResponse:
    return ApiMetaResponse(
        api_version=settings.api_version,
        environment=settings.environment,
        timestamp_policy="UTC ISO 8601",
    )


@app.get("/api/config/shop", response_model=ShopConfigResponse, tags=["configuration"])
def shop_config() -> ShopConfigResponse:
    return ShopConfigResponse(
        timezone=settings.shop_timezone,
        currency=settings.currency,
        odometer_unit=settings.odometer_unit,
    )


@app.post("/api/auth/login")
def login(payload: LoginRequest) -> dict[str, Any]:
    user = find_user(payload.email)
    if user is None or not verify_password(payload.password, user):
        raise_api_error(
            "AUTHENTICATION_REQUIRED",
            "Invalid email or password.",
            status.HTTP_401_UNAUTHORIZED,
        )
    token = create_access_token(user)
    record_audit("STAFF_LOGIN", user.user_id, {"email": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": sanitize_user_payload(user),
    }


@app.get("/api/auth/me")
def auth_me(user: StaffUser = Depends(get_current_user)) -> dict[str, Any]:
    return sanitize_user_payload(user)


@app.get("/api/admin/staff")
def list_staff(user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER))) -> list[dict[str, Any]]:
    return [sanitize_user_payload(staff) for staff in STAFF_USERS]


@app.post("/api/admin/audit/events")
def create_admin_audit_event(
    payload: dict[str, Any], user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER))
) -> dict[str, Any]:
    event_type = payload.get("event_type") or "ADMIN_EVENT"
    record_audit(event_type, user.user_id, payload)
    return {"event_type": event_type, "actor_user_id": user.user_id, "occurred_at": iso_utc()}


@app.get("/api/audit/events")
def list_audit_events(user: StaffUser = Depends(get_current_user)) -> list[dict[str, Any]]:
    return AUDIT_EVENTS


@app.post("/api/customers", status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreateRequest, user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR))) -> dict[str, Any]:
    customer_id = uuid.uuid4().hex
    customer = {
        "customer_id": customer_id,
        "full_name": payload.full_name,
        "mobile_number": payload.mobile_number,
        "email": payload.email,
        "preferred_contact_method": payload.preferred_contact_method,
        "status": payload.status,
        "created_at": iso_utc(),
        "updated_at": iso_utc(),
    }
    CUSTOMERS[customer_id] = customer
    record_audit("CUSTOMER_CREATED", user.user_id, {"customer_id": customer_id})
    return customer


@app.get("/api/customers/{customer_id}")
def get_customer(customer_id: str, user: StaffUser = Depends(get_current_user)) -> dict[str, Any]:
    customer = CUSTOMERS.get(customer_id)
    if customer is None:
        raise_api_error("CUSTOMER_NOT_FOUND", "Customer not found.", status.HTTP_404_NOT_FOUND)
    return customer


@app.get("/api/vehicles")
def list_vehicles(
    search: str | None = Query(default=None),
    user: StaffUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    items = list(VEHICLES.values())
    if search:
        term = search.strip().lower()
        items = [
            vehicle
            for vehicle in items
            if term in (vehicle.get("plate_number") or "").lower()
            or term in (vehicle.get("vin_chassis_number") or "").lower()
            or term in (vehicle.get("make") or "").lower()
            or term in (vehicle.get("model") or "").lower()
        ]
    return items


@app.get("/api/vehicles/{vehicle_id}")
def get_vehicle(vehicle_id: str, user: StaffUser = Depends(get_current_user)) -> dict[str, Any]:
    return get_vehicle_or_404(vehicle_id)


@app.post("/api/vehicles", status_code=status.HTTP_201_CREATED)
def create_vehicle(payload: VehicleCreateRequest, user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR))) -> dict[str, Any]:
    customer = CUSTOMERS.get(payload.customer_id)
    if customer is None:
        raise_api_error("CUSTOMER_NOT_FOUND", "Customer not found.", status.HTTP_404_NOT_FOUND)
    vehicle_id = uuid.uuid4().hex
    vehicle = {
        "vehicle_id": vehicle_id,
        "customer_id": payload.customer_id,
        "plate_number": payload.plate_number,
        "vin_chassis_number": payload.vin_chassis_number,
        "make": payload.make,
        "model": payload.model,
        "year": payload.year,
        "color": payload.color,
        "current_odometer": payload.current_odometer,
        "created_at": iso_utc(),
        "updated_at": iso_utc(),
        "readings": [
            {
                "value": payload.current_odometer,
                "unit": settings.odometer_unit,
                "recorded_at": iso_utc(),
                "source_record": "INITIAL_RECORD",
                "is_correction": False,
            }
        ]
        if payload.current_odometer is not None
        else [],
    }
    VEHICLES[vehicle_id] = vehicle
    record_audit("VEHICLE_CREATED", user.user_id, {"vehicle_id": vehicle_id})
    return vehicle


@app.patch("/api/vehicles/{vehicle_id}")
def patch_vehicle(
    vehicle_id: str,
    payload: VehiclePatchRequest,
    user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR)),
) -> dict[str, Any]:
    vehicle = get_vehicle_or_404(vehicle_id)
    if payload.plate_number is not None:
        vehicle["plate_number"] = payload.plate_number
    if payload.color is not None:
        vehicle["color"] = payload.color
    if payload.make is not None:
        vehicle["make"] = payload.make
    if payload.model is not None:
        vehicle["model"] = payload.model
    if payload.year is not None:
        vehicle["year"] = payload.year
    if payload.vin_chassis_number is not None:
        vehicle["vin_chassis_number"] = payload.vin_chassis_number
    vehicle["updated_at"] = iso_utc()
    record_audit("VEHICLE_UPDATED", user.user_id, {"vehicle_id": vehicle_id})
    return vehicle


@app.post("/api/vehicles/{vehicle_id}/odometer/readings")
def add_odometer_reading(
    vehicle_id: str,
    payload: OdometerReadingRequest,
    user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR, StaffRole.TECHNICIAN_PAINTER)),
) -> dict[str, Any]:
    vehicle = get_vehicle_or_404(vehicle_id)
    current = vehicle.get("current_odometer")
    if current is not None and payload.value < current:
        raise_api_error("ODOMETER_REGRESSION", "Odometer reading regressed below the current reading.", status.HTTP_400_BAD_REQUEST)
    reading = {
        "value": payload.value,
        "unit": settings.odometer_unit,
        "recorded_at": iso_utc(),
        "source_record": payload.source_record,
        "is_correction": False,
    }
    vehicle.setdefault("readings", []).append(reading)
    vehicle["current_odometer"] = payload.value
    vehicle["updated_at"] = iso_utc()
    record_audit("ODOMETER_READING", user.user_id, {"vehicle_id": vehicle_id, "value": payload.value})
    return vehicle


@app.post("/api/vehicles/{vehicle_id}/odometer/corrections", status_code=status.HTTP_201_CREATED)
def add_odometer_correction(
    vehicle_id: str,
    payload: OdometerCorrectionRequest,
    user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR)),
) -> dict[str, Any]:
    vehicle = get_vehicle_or_404(vehicle_id)
    if payload.corrected_value < 0:
        raise_api_error("INVALID_ODOMETER", "Corrected odometer must be non-negative.", status.HTTP_400_BAD_REQUEST)
    correction = {
        "value": payload.corrected_value,
        "unit": settings.odometer_unit,
        "recorded_at": iso_utc(),
        "source_record": "ODOMETER_CORRECTION",
        "is_correction": True,
        "previous_value": payload.previous_value,
        "corrected_value": payload.corrected_value,
        "reason": payload.reason,
        "actor_user_id": payload.actor_user_id,
    }
    vehicle.setdefault("readings", []).append(correction)
    vehicle["current_odometer"] = payload.corrected_value
    vehicle["updated_at"] = iso_utc()
    record_audit("ODOMETER_CORRECTION", user.user_id, {"vehicle_id": vehicle_id, "corrected_value": payload.corrected_value})
    return vehicle


@app.post("/api/intakes", status_code=status.HTTP_201_CREATED)
def create_intake(payload: IntakeCreateRequest, user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR))) -> dict[str, Any]:
    vehicle = get_vehicle_or_404(payload.vehicle_id)
    existing = next((entry for entry in INTAKES.values() if entry["vehicle_id"] == payload.vehicle_id and entry["status"] == IntakeStatus.DRAFT), None)
    if existing is not None:
        return existing
    intake_id = uuid.uuid4().hex
    intake = {
        "intake_id": intake_id,
        "vehicle_id": payload.vehicle_id,
        "notes": payload.notes,
        "status": IntakeStatus.DRAFT.value,
        "created_at": iso_utc(),
        "updated_at": iso_utc(),
    }
    INTAKES[intake_id] = intake
    record_audit("INTAKE_CREATED", user.user_id, {"intake_id": intake_id, "vehicle_id": payload.vehicle_id})
    return intake


@app.get("/api/intakes/{intake_id}")
def get_intake(intake_id: str, user: StaffUser = Depends(get_current_user)) -> dict[str, Any]:
    intake = INTAKES.get(intake_id)
    if intake is None:
        raise_api_error("INTAKE_NOT_FOUND", "Intake not found.", status.HTTP_404_NOT_FOUND)
    return intake


@app.post("/api/inspections", status_code=status.HTTP_201_CREATED)
def create_inspection(payload: InspectionCreateRequest, user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR, StaffRole.TECHNICIAN_PAINTER))) -> dict[str, Any]:
    intake = INTAKES.get(payload.intake_id)
    if intake is None:
        raise_api_error("INTAKE_NOT_FOUND", "Intake not found.", status.HTTP_404_NOT_FOUND)
    inspection_id = uuid.uuid4().hex
    inspection = {
        "inspection_id": inspection_id,
        "intake_id": payload.intake_id,
        "vehicle_id": intake["vehicle_id"],
        "status": InspectionStatus.DRAFT.value,
        "concerns": [concern.model_dump() for concern in payload.concerns],
        "customer_notes": payload.customer_notes,
        "technician_notes": payload.technician_notes,
        "overall_condition": payload.overall_condition,
        "created_at": iso_utc(),
        "updated_at": iso_utc(),
    }
    INSPECTIONS[inspection_id] = inspection
    record_audit("INSPECTION_CREATED", user.user_id, {"inspection_id": inspection_id, "intake_id": payload.intake_id})
    return inspection


@app.get("/api/inspections/{inspection_id}")
def get_inspection(inspection_id: str, user: StaffUser = Depends(get_current_user)) -> dict[str, Any]:
    return get_inspection_or_404(inspection_id)


@app.post("/api/inspections/{inspection_id}/complete")
def complete_inspection(inspection_id: str, user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR, StaffRole.TECHNICIAN_PAINTER))) -> dict[str, Any]:
    inspection = get_inspection_or_404(inspection_id)
    inspection["status"] = InspectionStatus.COMPLETED.value
    inspection["completed_at"] = iso_utc()
    inspection["updated_at"] = iso_utc()
    record_audit("INSPECTION_COMPLETED", user.user_id, {"inspection_id": inspection_id})
    return inspection


@app.patch("/api/inspections/{inspection_id}")
def patch_inspection(
    inspection_id: str,
    payload: dict[str, Any],
    user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR, StaffRole.TECHNICIAN_PAINTER)),
) -> dict[str, Any]:
    inspection = get_inspection_or_404(inspection_id)
    if inspection.get("status") == InspectionStatus.COMPLETED.value:
        raise_api_error("INSPECTION_LOCKED", "Completed inspections are immutable.", status.HTTP_409_CONFLICT)
    for key, value in payload.items():
        if key == "concerns":
            inspection["concerns"] = value
        else:
            inspection[key] = value
    inspection["updated_at"] = iso_utc()
    record_audit("INSPECTION_UPDATED", user.user_id, {"inspection_id": inspection_id})
    return inspection


@app.post("/api/inspections/{inspection_id}/photos", status_code=status.HTTP_201_CREATED)
def upload_inspection_photo(
    inspection_id: str,
    file: UploadFile = File(...),
    user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR, StaffRole.TECHNICIAN_PAINTER)),
) -> dict[str, Any]:
    get_inspection_or_404(inspection_id)
    content = file.file.read()
    if len(content) > 10 * 1024 * 1024:
        raise_api_error("FILE_TOO_LARGE", "File exceeds 10MB limit.", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
            width, height = image.size
    except Exception:  # pragma: no cover - defensive validation
        raise_api_error(
            "UNSUPPORTED_MEDIA_TYPE",
            "Uploaded file is not a valid image.",
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )
    if file.content_type not in {"image/png", "image/jpeg", "image/gif"}:
        raise_api_error("UNSUPPORTED_MEDIA_TYPE", "Only PNG, JPEG, and GIF uploads are permitted.", status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
    if width <= 0 or height <= 0:
        raise_api_error("INVALID_IMAGE", "Image dimensions are invalid.", status.HTTP_400_BAD_REQUEST)
    key = f"inspections/{uuid.uuid4().hex}.{file.filename.rsplit('.', 1)[-1].lower() or 'png'}"
    token = uuid.uuid4().hex
    SIGNED_PHOTOS[token] = {"storage_key": key, "content": content, "content_type": file.content_type}
    url = f"http://testserver/api/inspection-photos/{token}?token={token}"
    payload = {
        "inspection_id": inspection_id,
        "storage_key": key,
        "content_type": file.content_type,
        "width": width,
        "height": height,
        "uploader_user_id": user.user_id,
        "url": url,
    }
    record_audit("INSPECTION_PHOTO_UPLOADED", user.user_id, {"inspection_id": inspection_id, "storage_key": key})
    return payload


@app.get("/api/inspection-photos/{token}")
def get_signed_photo(token: str) -> Response:
    entry = SIGNED_PHOTOS.get(token)
    if entry is None:
        raise_api_error("PHOTO_NOT_FOUND", "Photo was not found.", status.HTTP_404_NOT_FOUND)
    return Response(content=entry["content"], media_type=entry["content_type"])


@app.post("/api/jobs", status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreateRequest, user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR))) -> dict[str, Any]:
    inspection = get_inspection_or_404(payload.inspection_id)
    job_id = uuid.uuid4().hex
    snapshot = {
        "inspection_id": inspection["inspection_id"],
        "vehicle_id": inspection.get("vehicle_id"),
        "concerns": deepcopy(inspection.get("concerns", [])),
        "customer_notes": inspection.get("customer_notes"),
        "technician_notes": inspection.get("technician_notes"),
        "overall_condition": inspection.get("overall_condition"),
    }
    history = [{
        "previous_status": None,
        "new_status": JobStatus.DRAFT.value,
        "actor_user_id": user.user_id,
        "occurred_at": iso_utc(),
        "reason": "Job created",
    }]
    job = {
        "job_id": job_id,
        "job_number": f"JOB-{job_id[:8].upper()}",
        "inspection_id": payload.inspection_id,
        "vehicle_id": payload.vehicle_id or inspection["vehicle_id"],
        "job_type": payload.job_type,
        "description": payload.description,
        "status": JobStatus.DRAFT.value,
        "estimated_cost": payload.estimated_cost,
        "approved_cost": payload.estimated_cost,
        "actual_cost": None,
        "scheduled_start": None,
        "scheduled_end": None,
        "actual_completion_date": None,
        "customer_notes": payload.customer_notes,
        "technician_notes": payload.technician_notes,
        "inspection_snapshot": snapshot,
        "status_history": history,
        "created_at": iso_utc(),
        "updated_at": iso_utc(),
    }
    JOBS[job_id] = job
    record_audit("JOB_CREATED", user.user_id, {"job_id": job_id, "inspection_id": payload.inspection_id})
    return job


@app.post("/api/inspections/{inspection_id}/jobs", status_code=status.HTTP_201_CREATED)
def create_job_from_inspection(inspection_id: str, user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR))) -> dict[str, Any]:
    inspection = get_inspection_or_404(inspection_id)
    return create_job(JobCreateRequest(inspection_id=inspection_id, vehicle_id=inspection["vehicle_id"]), user)


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str, user: StaffUser = Depends(get_current_user)) -> dict[str, Any]:
    return get_job_or_404(job_id)


@app.patch("/api/jobs/{job_id}")
def update_job(
    job_id: str,
    payload: dict[str, Any],
    user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR)),
) -> dict[str, Any]:
    job = get_job_or_404(job_id)
    for key, value in payload.items():
        if key != "status_history":
            job[key] = value
    job["updated_at"] = iso_utc()
    record_audit("JOB_UPDATED", user.user_id, {"job_id": job_id})
    return job


@app.post("/api/jobs/{job_id}/status")
@app.patch("/api/jobs/{job_id}/status")
def change_job_status(
    job_id: str,
    payload: JobStatusRequest,
    user: StaffUser = Depends(get_current_user),
) -> dict[str, Any]:
    job = get_job_or_404(job_id)
    current_status = job["status"]
    target_status = payload.status.upper()
    if not allowed_transition(user, current_status, target_status):
        raise_api_error("FORBIDDEN", "This status transition is not permitted for the current role.", status.HTTP_403_FORBIDDEN)
    previous_status = current_status
    job["status"] = target_status
    job.setdefault("status_history", []).append(
        {
            "previous_status": previous_status,
            "new_status": target_status,
            "actor_user_id": user.user_id,
            "occurred_at": iso_utc(),
            "reason": payload.reason,
        }
    )
    job["updated_at"] = iso_utc()
    if target_status == JobStatus.COMPLETED.value:
        job["actual_completion_date"] = iso_utc()
    record_audit("JOB_STATUS_CHANGED", user.user_id, {"job_id": job_id, "status": target_status})
    return job


@app.get("/api/jobs")
def list_jobs(user: StaffUser = Depends(get_current_user)) -> list[dict[str, Any]]:
    return list(JOBS.values())


def get_service_or_404(service_id: str) -> dict[str, Any]:
    service = SERVICES.get(service_id)
    if service is None:
        raise_api_error("SERVICE_NOT_FOUND", "Service record not found.", status.HTTP_404_NOT_FOUND)
    return service


def schedule_specifications(service: dict[str, Any]) -> list[dict[str, Any]]:
    specifications = []
    for item in service.get("items", []):
        due_date = item.get("next_due_date")
        due_odometer = item.get("next_due_odometer")
        if due_date is None and due_odometer is None:
            continue
        rule_type = item.get("rule_type")
        if rule_type is None:
            rule_type = (
                ScheduleRuleType.WHICHEVER_COMES_FIRST.value
                if due_date is not None and due_odometer is not None
                else ScheduleRuleType.DATE_ONLY.value
                if due_date is not None
                else ScheduleRuleType.ODOMETER_ONLY.value
            )
        try:
            rule_type = ScheduleRuleType(rule_type).value
        except ValueError:
            raise_api_error("INVALID_SCHEDULE_RULE", "Unknown maintenance schedule rule.", status.HTTP_400_BAD_REQUEST)
        if rule_type in {ScheduleRuleType.DATE_ONLY.value, ScheduleRuleType.WHICHEVER_COMES_LAST.value} and due_date is None:
            raise_api_error("INVALID_SCHEDULE", "This rule requires a due date.", status.HTTP_400_BAD_REQUEST)
        if rule_type in {ScheduleRuleType.ODOMETER_ONLY.value, ScheduleRuleType.WHICHEVER_COMES_LAST.value} and due_odometer is None:
            raise_api_error("INVALID_SCHEDULE", "This rule requires a due odometer.", status.HTTP_400_BAD_REQUEST)
        if rule_type == ScheduleRuleType.WHICHEVER_COMES_FIRST.value and (due_date is None or due_odometer is None):
            raise_api_error("INVALID_SCHEDULE", "This rule requires a due date and odometer.", status.HTTP_400_BAD_REQUEST)
        specifications.append(
            {
                "maintenance_type": item.get("maintenance_type") or item.get("service_category"),
                "due_date": due_date,
                "due_odometer": due_odometer,
                "rule_type": rule_type,
                "source_service_item_id": item["service_item_id"],
            }
        )
    return specifications


def evaluate_schedule(schedule: dict[str, Any], evaluated_at: datetime, odometer: int) -> str:
    current_date = evaluated_at.astimezone(UTC).date()
    due_date = date.fromisoformat(schedule["due_date"]) if schedule.get("due_date") else None
    due_odometer = schedule.get("due_odometer")
    date_due = due_date is not None and current_date >= due_date
    odometer_due = due_odometer is not None and odometer >= due_odometer
    date_overdue = due_date is not None and current_date > due_date
    odometer_overdue = due_odometer is not None and odometer > due_odometer
    rule_type = schedule["rule_type"]
    if rule_type == ScheduleRuleType.DATE_ONLY.value:
        due, overdue = date_due, date_overdue
    elif rule_type == ScheduleRuleType.ODOMETER_ONLY.value:
        due, overdue = odometer_due, odometer_overdue
    elif rule_type == ScheduleRuleType.WHICHEVER_COMES_FIRST.value:
        due, overdue = date_due or odometer_due, date_overdue or odometer_overdue
    else:
        due, overdue = date_due and odometer_due, date_overdue and odometer_overdue
    return ScheduleStatus.OVERDUE.value if overdue else ScheduleStatus.DUE.value if due else ScheduleStatus.PLANNED.value


def schedule_history_entry(previous_status: str | None, new_status: str, actor_user_id: str, reason: str) -> dict[str, Any]:
    return {
        "previous_status": previous_status,
        "new_status": new_status,
        "actor_user_id": actor_user_id,
        "occurred_at": iso_utc(),
        "reason": reason,
    }


@app.post("/api/services", status_code=status.HTTP_201_CREATED)
@app.post("/api/service-records", status_code=status.HTTP_201_CREATED)
def create_service_record(
    payload: ServiceRecordRequest,
    user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR, StaffRole.TECHNICIAN_PAINTER)),
) -> dict[str, Any]:
    get_vehicle_or_404(payload.vehicle_id)
    service_id = uuid.uuid4().hex
    items = []
    for item in payload.items:
        item_data = item.model_dump(mode="json")
        item_data["service_item_id"] = uuid.uuid4().hex
        items.append(item_data)
    parts = []
    for part in payload.parts:
        part_data = part.model_dump(mode="json")
        part_data["service_part_id"] = uuid.uuid4().hex
        part_data["total_cost"] = round(part.quantity * part.unit_cost, 2)
        parts.append(part_data)
    calculated_parts_cost = round(sum(part["total_cost"] for part in parts), 2)
    service = {
        "service_id": service_id,
        "vehicle_id": payload.vehicle_id,
        "service_date": payload.service_date.isoformat(),
        "odometer_reading": payload.odometer_reading,
        "service_type": payload.service_type,
        "description": payload.description,
        "status": ServiceStatus.DRAFT.value,
        "labor_cost": payload.labor_cost,
        "parts_cost": calculated_parts_cost if payload.parts else payload.parts_cost or 0,
        "total_cost": round(payload.labor_cost + calculated_parts_cost + sum(item["cost"] for item in items), 2),
        "recommendations": payload.recommendations,
        "items": items,
        "parts": parts,
        "created_at": iso_utc(),
        "updated_at": iso_utc(),
    }
    SERVICES[service_id] = service
    record_audit("SERVICE_CREATED", user.user_id, {"service_id": service_id, "vehicle_id": payload.vehicle_id})
    return service


@app.get("/api/services/{service_id}")
@app.get("/api/service-records/{service_id}")
def get_service_record(service_id: str, user: StaffUser = Depends(get_current_user)) -> dict[str, Any]:
    return get_service_or_404(service_id)


@app.patch("/api/services/{service_id}")
@app.patch("/api/service-records/{service_id}")
def update_service_record(
    service_id: str,
    payload: dict[str, Any],
    user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR, StaffRole.TECHNICIAN_PAINTER)),
) -> dict[str, Any]:
    service = get_service_or_404(service_id)
    if service["status"] != ServiceStatus.DRAFT.value:
        raise_api_error("SERVICE_LOCKED", "Completed or cancelled service records are immutable.", status.HTTP_409_CONFLICT)
    if payload.get("vehicle_id") is not None and payload["vehicle_id"] != service["vehicle_id"]:
        raise_api_error("SERVICE_VEHICLE_IMMUTABLE", "A service record cannot change vehicles.", status.HTTP_400_BAD_REQUEST)
    editable_fields = {
        "service_date",
        "odometer_reading",
        "service_type",
        "description",
        "labor_cost",
        "recommendations",
        "items",
        "parts",
    }
    for key, value in payload.items():
        if key in editable_fields:
            service[key] = value
    service["updated_at"] = iso_utc()
    record_audit("SERVICE_UPDATED", user.user_id, {"service_id": service_id})
    return service


@app.post("/api/services/{service_id}/complete")
@app.post("/api/service-records/{service_id}/complete")
def complete_service_record(
    service_id: str,
    user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR, StaffRole.TECHNICIAN_PAINTER)),
) -> dict[str, Any]:
    service = get_service_or_404(service_id)
    if service["status"] == ServiceStatus.COMPLETED.value:
        return service
    if service["status"] == ServiceStatus.CANCELLED.value:
        raise_api_error("SERVICE_NOT_COMPLETABLE", "Cancelled service records cannot be completed.", status.HTTP_409_CONFLICT)
    vehicle = get_vehicle_or_404(service["vehicle_id"])
    specifications = schedule_specifications(service)
    needs_odometer = any(spec["due_odometer"] is not None for spec in specifications)
    if needs_odometer and service.get("odometer_reading") is None:
        raise_api_error("ODOMETER_REQUIRED", "An odometer reading is required for this schedule.", status.HTTP_400_BAD_REQUEST)
    current_odometer = vehicle.get("current_odometer")
    if service.get("odometer_reading") is not None and current_odometer is not None and service["odometer_reading"] < current_odometer:
        raise_api_error("ODOMETER_REGRESSION", "Odometer reading regressed below the current reading.", status.HTTP_400_BAD_REQUEST)

    updated_vehicle = deepcopy(vehicle)
    updated_schedules = deepcopy(MAINTENANCE_SCHEDULES)
    updated_service = deepcopy(service)
    if service.get("odometer_reading") is not None:
        updated_vehicle.setdefault("readings", []).append(
            {
                "value": service["odometer_reading"],
                "unit": settings.odometer_unit,
                "recorded_at": iso_utc(),
                "source_record": service_id,
                "is_correction": False,
            }
        )
        updated_vehicle["current_odometer"] = service["odometer_reading"]
        updated_vehicle["updated_at"] = iso_utc()
    updated_service["status"] = ServiceStatus.COMPLETED.value
    updated_service["completed_at"] = iso_utc()
    updated_service["completed_by"] = user.user_id
    updated_service["updated_at"] = iso_utc()
    new_schedule_ids = []
    for specification in specifications:
        schedule_id = uuid.uuid4().hex
        for existing in updated_schedules.values():
            if (
                existing["vehicle_id"] == service["vehicle_id"]
                and existing["maintenance_type"] == specification["maintenance_type"]
                and existing["status"] in {ScheduleStatus.PLANNED.value, ScheduleStatus.DUE.value, ScheduleStatus.OVERDUE.value}
            ):
                existing["status"] = ScheduleStatus.SKIPPED.value
                existing["superseded_by_schedule_id"] = schedule_id
                existing.setdefault("state_history", []).append(
                    schedule_history_entry(existing["state_history"][-1]["new_status"], ScheduleStatus.SKIPPED.value, user.user_id, "Superseded by completed service")
                )
        schedule = {
            "schedule_id": schedule_id,
            "vehicle_id": service["vehicle_id"],
            "service_record_id": service_id,
            "maintenance_type": specification["maintenance_type"],
            "due_date": specification["due_date"],
            "due_odometer": specification["due_odometer"],
            "rule_type": specification["rule_type"],
            "status": ScheduleStatus.PLANNED.value,
            "source_service_item_id": specification["source_service_item_id"],
            "superseded_by_schedule_id": None,
            "state_history": [schedule_history_entry(None, ScheduleStatus.PLANNED.value, user.user_id, "Schedule created")],
            "created_at": iso_utc(),
            "updated_at": iso_utc(),
        }
        updated_schedules[schedule_id] = schedule
        new_schedule_ids.append(schedule_id)
    updated_service["schedule_ids"] = new_schedule_ids
    VEHICLES[service["vehicle_id"]] = updated_vehicle
    SERVICES[service_id] = updated_service
    MAINTENANCE_SCHEDULES.clear()
    MAINTENANCE_SCHEDULES.update(updated_schedules)
    record_audit("SERVICE_COMPLETED", user.user_id, {"service_id": service_id, "schedule_ids": new_schedule_ids})
    return updated_service


@app.post("/api/services/{service_id}/cancel")
@app.post("/api/service-records/{service_id}/cancel")
def cancel_service_record(
    service_id: str,
    payload: ServiceCancelRequest | None = None,
    user: StaffUser = Depends(require_roles(StaffRole.ADMIN_MANAGER, StaffRole.SERVICE_ADVISOR)),
) -> dict[str, Any]:
    service = get_service_or_404(service_id)
    if service["status"] != ServiceStatus.DRAFT.value:
        raise_api_error("SERVICE_LOCKED", "Only draft service records can be cancelled.", status.HTTP_409_CONFLICT)
    service["status"] = ServiceStatus.CANCELLED.value
    service["cancelled_at"] = iso_utc()
    service["cancelled_by"] = user.user_id
    service["cancellation_reason"] = payload.reason if payload else None
    service["updated_at"] = iso_utc()
    record_audit("SERVICE_CANCELLED", user.user_id, {"service_id": service_id})
    return service


@app.get("/api/maintenance-schedules")
def list_maintenance_schedules(
    vehicle_id: str | None = None,
    user: StaffUser = Depends(get_current_user),
) -> list[dict[str, Any]]:
    schedules = list(MAINTENANCE_SCHEDULES.values())
    return [schedule for schedule in schedules if vehicle_id is None or schedule["vehicle_id"] == vehicle_id]


@app.get("/api/maintenance-schedules/{schedule_id}")
def get_maintenance_schedule(schedule_id: str, user: StaffUser = Depends(get_current_user)) -> dict[str, Any]:
    schedule = MAINTENANCE_SCHEDULES.get(schedule_id)
    if schedule is None:
        raise_api_error("SCHEDULE_NOT_FOUND", "Maintenance schedule not found.", status.HTTP_404_NOT_FOUND)
    return schedule


@app.post("/api/maintenance-schedules/{schedule_id}/evaluate")
def evaluate_maintenance_schedule(
    schedule_id: str,
    payload: ScheduleEvaluationRequest | None = None,
    user: StaffUser = Depends(get_current_user),
) -> dict[str, Any]:
    schedule = MAINTENANCE_SCHEDULES.get(schedule_id)
    if schedule is None:
        raise_api_error("SCHEDULE_NOT_FOUND", "Maintenance schedule not found.", status.HTTP_404_NOT_FOUND)
    vehicle = get_vehicle_or_404(schedule["vehicle_id"])
    evaluated_at = (payload.evaluated_at if payload and payload.evaluated_at else datetime.now(UTC))
    odometer = payload.odometer if payload and payload.odometer is not None else vehicle.get("current_odometer") or 0
    result = deepcopy(schedule)
    result["evaluated_status"] = evaluate_schedule(schedule, evaluated_at, odometer)
    result["evaluated_at"] = iso_utc(evaluated_at)
    result["evaluated_odometer"] = odometer
    return result
