"""SQLAlchemy models for AutoTrack."""

from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from sqlalchemy import Integer, String, Float, DateTime

Base = declarative_base()


class Customer(Base):
    """Customer model representing a shop customer."""
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str]
    mobile_number: Mapped[str]
    email: Mapped[str]
    address: Mapped[str] = ""

    # Contact preferences
    preferred_contact_method: Mapped[str] = "sms"  # sms, email, messenger, push
    status: Mapped[str] = "active"  # active, inactive

    # Timestamps
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    # Relationships (lazy loading strings for backward compat)
    vehicles = "list[Vehicle]"  # back-populated by Vehicle.customer relationship


class Vehicle(Base):
    """Vehicle model representing a customer's vehicle."""
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int]
    plate_number: Mapped[str]
    vin_chassis_number: Mapped[str] = ""
    make: Mapped[str]
    model: Mapped[str]
    variant: Mapped[str] = ""
    year: Mapped[int]
    color: Mapped[str] = ""
    fuel_type: Mapped[str] = ""
    transmission: Mapped[str] = ""
    current_odometer: Mapped[float] = 0.0
    notes: Mapped[str] = ""

    # Data quality: odometer tracking

    # Relationships
    customer = "Customer"  # back_populates="vehicles"
    inspections = "list[Inspection]"  # back_populates="vehicle"
    paint_jobs = "list[PaintJob]"  # back_populates="vehicle"
    service_records = "list[ServiceRecord]"  # back_populates="vehicle"


class Inspection(Base):
    """Inspection model recording vehicle condition at intake."""
    __tablename__ = "vehicle_inspections"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int]
    inspection_date: Mapped[datetime]
    odometer_reading: Mapped[float]
    fuel_level: Mapped[float] = 100.0
    overall_condition: Mapped[str] = ""  # e.g., "Excellent", "Good", "Fair", "Poor"
    customer_notes: Mapped[str] = ""
    technician_notes: Mapped[str] = ""
    created_by: Mapped[int] = 0  # staff member ID

    # Timestamps
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    # Relationships
    vehicle = "Vehicle"  # back_populates="inspections"
    items = "list[InspectionItem]"  # back_populates="inspection"
    photos = "list[InspectionPhoto]"  # back_populates="inspection_item"


class InspectionItem(Base):
    """Individual concern item from a digital inspection."""
    __tablename__ = "inspection_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    inspection_id: Mapped[int]
    vehicle_area: Mapped[str]  # e.g., "Front Bumper", "Hood", etc.
    condition_type: Mapped[str]  # e.g., SCRATCH, DENT, PAINT_FADE, etc.
    severity: Mapped[str]  # e.g., MINOR, MODERATE, MAJOR, CRITICAL
    requested_work: Mapped[str] = ""
    technician_notes: Mapped[str] = ""
    recommended_action: Mapped[str] = ""

    # Relationships
    inspection = "Inspection"  # back_populates="items"


class InspectionPhoto(Base):
    """Photo linked to an inspection item."""
    __tablename__ = "inspection_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    inspection_item_id: Mapped[int]
    storage_path: Mapped[str]  # Supabase storage key/path
    photo_type: Mapped[str] = "inspection"  # inspection, paint_job, other
    caption: Mapped[str] = ""
    uploaded_by: Mapped[int] = 0  # staff member ID

    # Timestamps
    created_at: Mapped[datetime]

    # Relationships
    inspection_item = "InspectionItem"  # back_populates="photos"


class PaintJob(Base):
    """Paint/body repair job model."""
    __tablename__ = "paint_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int]
    inspection_id: Mapped[int]
    job_number: Mapped[str]  # Auto-generated
    job_type: Mapped[str] = ""  # e.g., "Full panel repaint", "Spot repair"
    description: Mapped[str] = ""
    status: Mapped[str] = "DRAFT"  # DRAFT, INSPECTION, ESTIMATE, CUSTOMER_APPROVAL, SCHEDULED, IN_PROGRESS, QUALITY_CHECK, READY_FOR_RELEASE, COMPLETED, CANCELLED
    estimated_cost: Mapped[float] = 0.0
    approved_cost: Mapped[float] = 0.0
    actual_cost: Mapped[float] = 0.0
    scheduled_start: Mapped[datetime] = None
    scheduled_end: Mapped[datetime] = None
    actual_completion_date: Mapped[datetime] = None
    customer_notes: Mapped[str] = ""
    technician_notes: Mapped[str] = ""

    # Status history audit
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]

    # Relationships
    vehicle = "Vehicle"  # back_populates="paint_jobs"
    inspection = "Inspection"  # back_populates="paint_job snapshot"
    items = "list[PaintJobItem]"  # back_populates="paint_job"
    status_history = "list[PaintJobStatusHistory]"  # back-populated via trigger/audit


class PaintJobItem(Base):
    """Individual item within a paint job."""
    __tablename__ = "paint_job_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    paint_job_id: Mapped[int]
    vehicle_area: Mapped[str]
    service_type: Mapped[str] = ""  # e.g., SANDING, BODY_REPAIR, DENT_REPAIR, etc.
    description: Mapped[str] = ""
    labor_cost: Mapped[float] = 0.0
    material_cost: Mapped[float] = 0.0
    quantity: Mapped[int] = 1
    total_cost: Mapped[float] = 0.0
    status: Mapped[str] = "pending"  # pending, in_progress, completed

    # Relationships
    paint_job = "PaintJob"  # back_populates="items"


class PaintJobStatusHistory(Base):
    """Audit trail for paint job status changes."""
    __tablename__ = "paint_job_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    paint_job_id: Mapped[int]
    previous_status: Mapped[str]
    new_status: Mapped[str]
    actor: Mapped[int]  # staff member ID
    occurred_at: Mapped[datetime]
    reason: Mapped[str] = ""


class ServiceRecord(Base):
    """PMS service record model."""
    __tablename__ = "service_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int]
    service_date: Mapped[datetime]
    odometer_reading: Mapped[float]
    service_type: Mapped[str] = ""  # e.g., PMS, OIL_CHANGE, BRAKE_SERVICE, etc.
    description: Mapped[str] = ""
    completed_at: Mapped[datetime] = None
    completed_by: Mapped[int] = 0  # staff member ID
    status: Mapped[str] = "DRAFT"  # DRAFT, COMPLETED, CANCELLED
    labor_cost: Mapped[float] = 0.0
    parts_cost: Mapped[float] = 0.0
    total_cost: Mapped[float] = 0.0
    recommendations: Mapped[str] = ""

    # Relationships
    vehicle = "Vehicle"  # back_populates="service_records"
    items = "list[ServiceItem]"  # back_populates="service_record"
    parts = "list[ServicePart]"  # back_populates="service_record"
    schedules = "list[MaintenanceSchedule]"  # back_populates="source_service_record"


class ServiceItem(Base):
    """Individual item within a service record."""
    __tablename__ = "service_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_record_id: Mapped[int]
    service_category: Mapped[str] = ""  # e.g., LABOR, PARTS, DIAGNOSTIC, etc.
    description: Mapped[str] = ""
    status: Mapped[str] = "pending"  # pending, completed
    cost: Mapped[float] = 0.0
    next_due_odometer: Mapped[float] = 0.0
    next_due_date: Mapped[datetime] = None
    rule_type: Mapped[str] = "ODOMETER_ONLY"  # DATE_ONLY, ODOMETER_ONLY, WHICHEVER_COMES_FIRST, WHICHEVER_COMES_LAST

    # Relationships
    service_record = "ServiceRecord"  # back_populates="items"


class ServicePart(Base):
    """Part used in a service record."""
    __tablename__ = "service_parts"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_record_id: Mapped[int]
    part_name: Mapped[str]
    part_number: Mapped[str] = ""
    quantity: Mapped[int] = 1
    unit_cost: Mapped[float] = 0.0
    total_cost: Mapped[float] = 0.0

    # Relationships
    service_record = "ServiceRecord"  # back_populates="parts"


class MaintenanceSchedule(Base):
    """Maintenance schedule generated from a service record."""
    __tablename__ = "maintenance_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int]
    service_record_id: Mapped[int]
    maintenance_type: Mapped[str] = ""  # e.g., OIL_CHANGE, BRAKE_INSPECTION, etc.
    due_date: Mapped[datetime]
    due_odometer: Mapped[float]
    interval_months: Mapped[int] = 0
    interval_km: Mapped[float] = 0.0
    rule_type: Mapped[str] = "WHICHEVER_COMES_FIRST"  # DATE_ONLY, ODOMETER_ONLY, WHICHEVER_COMES_FIRST, WHICHEVER_COMES_LAST
    status: Mapped[str] = "PLANNED"  # PLANNED, DUE, OVERDUE, COMPLETED, SKIPPED, CANCELLED
    source_service_item_id: Mapped[int] = 0
    completed_at: Mapped[datetime] = None
    completed_by: Mapped[int] = 0  # staff member ID
    superseded_by_schedule_id: Mapped[int] = 0
    notes: Mapped[str] = ""

    # Relationships
    vehicle = "Vehicle"  # back_populates="schedules"
    source_service_record = "ServiceRecord"  # back_populates="schedules"


class MaintenanceReminder(Base):
    """Reminder business event for a maintenance schedule."""
    __tablename__ = "maintenance_reminders"

    id: Mapped[int] = mapped_column(primary_key=True)
    maintenance_schedule_id: Mapped[int]
    customer_id: Mapped[int]
    vehicle_id: Mapped[int]
    stage: Mapped[str] = ""  # 30_DAYS, 7_DAYS, DUE_TODAY, OVERDUE
    scheduled_for: Mapped[datetime]
    generated_at: Mapped[datetime]
    status: Mapped[str] = "PENDING"  # PENDING, SENT, CANCELLED
    cancelled_at: Mapped[datetime] = None
    cancelled_reason: Mapped[str] = ""

    # Relationships
    maintenance_schedule = "MaintenanceSchedule"
    customer = "Customer"
    vehicle = "Vehicle"


class CustomerNotificationPreferences(Base):
    """Customer notification preference settings."""
    __tablename__ = "customer_notification_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int]
    sms_enabled: Mapped[bool] = True
    email_enabled: Mapped[bool] = True
    messenger_enabled: Mapped[bool] = True
    push_enabled: Mapped[bool] = True
    pms_reminders_enabled: Mapped[bool] = True
    marketing_enabled: Mapped[bool] = False
    timezone: Mapped[str] = "UTC"
    quiet_hours_start: Mapped[str] = "22:00"
    quiet_hours_end: Mapped[str] = "06:00"
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]


class Notification(Base):
    """Channel-specific notification delivery attempt."""
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int]
    vehicle_id: Mapped[int]
    maintenance_schedule_id: Mapped[int] = 0
    reminder_id: Mapped[int] = 0
    channel: Mapped[str] = ""  # SMS, EMAIL, MESSENGER_WHATSAPP
    stage: Mapped[str] = ""  # 30_DAYS, 7_DAYS, DUE_TODAY, OVERDUE
    scheduled_at: Mapped[datetime]
    sent_at: Mapped[datetime] = None
    attempt_count: Mapped[int] = 0
    next_attempt_at: Mapped[datetime] = None
    status: Mapped[str] = "PENDING"  # PENDING, PROCESSING, SENT, FAILED, CANCELLED
    provider_message_id: Mapped[str] = ""
    error_message: Mapped[str] = ""

    # Relationships
    customer = "Customer"
    vehicle = "Vehicle"


class NotificationAttempt(Base):
    """Individual provider call attempt for a notification."""
    __tablename__ = "notification_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    notification_id: Mapped[int]
    attempt_number: Mapped[int]
    attempted_at: Mapped[datetime]
    status: Mapped[str] = "PROCESSING"  # PROCESSING, SENT, FAILED
    provider_message_id: Mapped[str] = ""
    error_code: Mapped[str] = ""
    error_message: Mapped[str] = ""
    response_reference: Mapped[str] = ""

    # Relationships


class Technician(Base):
    """Technician/staff user model."""
    __tablename__ = "users"  # Using 'users' to avoid clash with Python 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str]
    email: Mapped[str]
    role: Mapped[str] = "TECHNICIAN_PAINTER"  # ADMIN_MANAGER, SERVICE_ADVISOR, TECHNICIAN_PAINTER, READ_ONLY
    is_active: Mapped[bool] = True
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]