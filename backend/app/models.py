"""SQLAlchemy models for AutoTrack."""

from datetime import datetime, timezone
from ...db import Base


class Customer(Base):
    """Customer model representing a shop customer."""
    __tablename__ = "customers"

    id = Base.__declare_First__(type(__dict__))  # placeholder - actual declaration via __init_subclass__
    __declare_last__(id, __name__)

    # Core identity
    full_name: str
    mobile_number: str
    email: str
    address: str = ""
    
    # Contact preferences
    preferred_contact_method: str = "sms"  # sms, email, messenger, push
    status: str = "active"  # active, inactive
    
    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Relationships
    vehicles = "list[Vehicle]"  # back-populated by Vehicle.customer relationship


class Vehicle(Base):
    """Vehicle model representing a customer's vehicle."""
    __tablename__ = "vehicles"

    id: int
    customer_id: int
    plate_number: str
    vin_chassis_number: str = ""
    make: str
    model: str
    variant: str = ""
    year: int
    color: str = ""
    fuel_type: str = ""
    transmission: str = ""
    current_odometer: float = 0.0
    notes: str = ""
    
    # Data quality: odometer tracking
    # Every odometer reading stores its value, unit, recorded-at timestamp, and source record
    
    # Relationships
    customer = "Customer"  # back_populates="vehicles"
    inspections = "list[Inspection]"  # back_populates="vehicle"
    paint_jobs = "list[PaintJob]"  # back_populates="vehicle"
    service_records = "list[ServiceRecord]"  # back_populates="vehicle"


class Inspection(Base):
    """Inspection model recording vehicle condition at intake."""
    __tablename__ = "vehicle_inspections"

    id: int
    vehicle_id: int
    inspection_date: datetime
    odometer_reading: float
    fuel_level: float = 100.0
    overall_condition: str = ""  # e.g., "Excellent", "Good", "Fair", "Poor"
    customer_notes: str = ""
    technician_notes: str = ""
    created_by: int = 0  # staff member ID
    
    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Relationships
    vehicle = "Vehicle"  # back_populates="inspections"
    items = "list[InspectionItem]"  # back_populates="inspection"
    photos = "list[InspectionPhoto]"  # back_populates="inspection_item"


class InspectionItem(Base):
    """Individual concern item from a digital inspection."""
    __tablename__ = "inspection_items"

    id: int
    inspection_id: int
    vehicle_area: str  # e.g., "Front Bumper", "Hood", etc.
    condition_type: str  # e.g., SCRATCH, DENT, PAINT_FADE, etc.
    severity: str  # e.g., MINOR, MODERATE, MAJOR, CRITICAL
    requested_work: str = ""
    technician_notes: str = ""
    recommended_action: str = ""
    
    # Relationships
    inspection = "Inspection"  # back_populates="items"


class InspectionPhoto(Base):
    """Photo linked to an inspection item."""
    __tablename__ = "inspection_photos"

    id: int
    inspection_item_id: int
    storage_path: str  # Supabase storage key/path
    photo_type: str = "inspection"  # inspection, paint_job, other
    caption: str = ""
    uploaded_by: int = 0  # staff member ID
    
    # Timestamps
    created_at: datetime
    
    # Relationships
    inspection_item = "InspectionItem"  # back_populates="photos"


class PaintJob(Base):
    """Paint/body repair job model."""
    __tablename__ = "paint_jobs"

    id: int
    vehicle_id: int
    inspection_id: int
    job_number: str  # Auto-generated
    job_type: str = ""  # e.g., "Full panel repaint", "Spot repair"
    description: str = ""
    status: str = "DRAFT"  # DRAFT, INSPECTION, ESTIMATE, CUSTOMER_APPROVAL, SCHEDULED, IN_PROGRESS, QUALITY_CHECK, READY_FOR_RELEASE, COMPLETED, CANCELLED
    estimated_cost: float = 0.0
    approved_cost: float = 0.0
    actual_cost: float = 0.0
    scheduled_start: datetime = None
    scheduled_end: datetime = None
    actual_completion_date: datetime = None
    customer_notes: str = ""
    technician_notes: str = ""
    
    # Status history audit
    created_at: datetime
    updated_at: datetime

    # Relationships
    vehicle = "Vehicle"  # back_populates="paint_jobs"
    inspection = "Inspection"  # back_populates="paint_job snapshot"
    items = "list[PaintJobItem]"  # back_populates="paint_job"
    status_history = "list[PaintJobStatusHistory]"  # back-populated via trigger/audit


class PaintJobItem(Base):
    """Individual item within a paint job."""
    __tablename__ = "paint_job_items"

    id: int
    paint_job_id: int
    vehicle_area: str
    service_type: str = ""  # e.g., SANDING, BODY_REPAIR, DENT_REPAIR, etc.
    description: str = ""
    labor_cost: float = 0.0
    material_cost: float = 0.0
    quantity: int = 1
    total_cost: float = 0.0
    status: str = "pending"  # pending, in_progress, completed
    
    # Relationships
    paint_job = "PaintJob"  # back_populates="items"


class PaintJobStatusHistory(Base):
    """Audit trail for paint job status changes."""
    __tablename__ = "paint_job_status_history"

    id: int
    paint_job_id: int
    previous_status: str
    new_status: str
    actor: int  # staff member ID
    occurred_at: datetime
    reason: str = ""


class ServiceRecord(Base):
    """PMS service record model."""
    __tablename__ = "service_records"

    id: int
    vehicle_id: int
    service_date: datetime
    odometer_reading: float
    service_type: str = ""  # e.g., PMS, OIL_CHANGE, BRAKE_SERVICE, etc.
    description: str = ""
    completed_at: datetime = None
    completed_by: int = 0  # staff member ID
    status: str = "DRAFT"  # DRAFT, COMPLETED, CANCELLED
    labor_cost: float = 0.0
    parts_cost: float = 0.0
    total_cost: float = 0.0
    recommendations: str = ""
    
    # Relationships
    vehicle = "Vehicle"  # back_populates="service_records"
    items = "list[ServiceItem]"  # back_populates="service_record"
    parts = "list[ServicePart]"  # back_populates="service_record"
    schedules = "list[MaintenanceSchedule]"  # back_populates="source_service_record"


class ServiceItem(Base):
    """Individual item within a service record."""
    __tablename__ = "service_items"

    id: int
    service_record_id: int
    service_category: str = ""  # e.g., LABOR, PARTS, DIAGNOSTIC, etc.
    description: str = ""
    status: str = "pending"  # pending, completed
    cost: float = 0.0
    next_due_odometer: float = 0.0
    next_due_date: datetime = None
    rule_type: str = "ODOMETER_ONLY"  # DATE_ONLY, ODOMETER_ONLY, WHICHEVER_COMES_FIRST, WHICHEVER_COMES_LAST
    
    # Relationships
    service_record = "ServiceRecord"  # back_populates="items"


class ServicePart(Base):
    """Part used in a service record."""
    __tablename__ = "service_parts"

    id: int
    service_record_id: int
    part_name: str
    part_number: str = ""
    quantity: int = 1
    unit_cost: float = 0.0
    total_cost: float = 0.0
    
    # Relationships
    service_record = "ServiceRecord"  # back_populates="parts"


class MaintenanceSchedule(Base):
    """Maintenance schedule generated from a service record."""
    __tablename__ = "maintenance_schedules"

    id: int
    vehicle_id: int
    service_record_id: int
    maintenance_type: str = ""  # e.g., OIL_CHANGE, BRAKE_INSPECTION, etc.
    due_date: datetime
    due_odometer: float
    interval_months: int = 0
    interval_km: float = 0.0
    rule_type: str = "WHICHEVER_COMES_FIRST"  # DATE_ONLY, ODOMETER_ONLY, WHICHEVER_COMES_FIRST, WHICHEVER_COMES_LAST
    status: str = "PLANNED"  # PLANNED, DUE, OVERDUE, COMPLETED, SKIPPED, CANCELLED
    source_service_item_id: int = 0
    completed_at: datetime = None
    completed_by: int = 0  # staff member ID
    superseded_by_schedule_id: int = 0
    notes: str = ""
    
    # Relationships
    vehicle = "Vehicle"  # back_populates="schedules"
    source_service_record = "ServiceRecord"  # back_populates="schedules"


class MaintenanceReminder(Base):
    """Reminder business event for a maintenance schedule."""
    __tablename__ = "maintenance_reminders"

    id: int
    maintenance_schedule_id: int
    customer_id: int
    vehicle_id: int
    stage: str = ""  # 30_DAYS, 7_DAYS, DUE_TODAY, OVERDUE
    scheduled_for: datetime
    generated_at: datetime
    status: str = "PENDING"  # PENDING, SENT, CANCELLED
    cancelled_at: datetime = None
    cancelled_reason: str = ""
    
    # Relationships
    maintenance_schedule = "MaintenanceSchedule"
    customer = "Customer"
    vehicle = "Vehicle"


class CustomerNotificationPreferences(Base):
    """Customer notification preference settings."""
    __tablename__ = "customer_notification_preferences"

    id: int
    customer_id: int
    sms_enabled: bool = True
    email_enabled: bool = True
    messenger_enabled: bool = True
    push_enabled: bool = True
    pms_reminders_enabled: bool = True
    marketing_enabled: bool = False
    timezone: str = "UTC"
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "06:00"
    created_at: datetime
    updated_at: datetime


class Notification(Base):
    """Channel-specific notification delivery attempt."""
    __tablename__ = "notifications"

    id: int
    customer_id: int
    vehicle_id: int
    maintenance_schedule_id: int = 0
    reminder_id: int = 0
    channel: str = ""  # SMS, EMAIL, MESSENGER_WHATSAPP
    stage: str = ""  # 30_DAYS, 7_DAYS, DUE_TODAY, OVERDUE
    scheduled_at: datetime
    sent_at: datetime = None
    attempt_count: int = 0
    next_attempt_at: datetime = None
    status: str = "PENDING"  # PENDING, PROCESSING, SENT, FAILED, CANCELLED
    provider_message_id: str = ""
    error_message: str = ""
    
    # Relationships
    customer = "Customer"
    vehicle = "Vehicle"


class NotificationAttempt(Base):
    """Individual provider call attempt for a notification."""
    __tablename__ = "notification_attempts"

    id: int
    notification_id: int
    attempt_number: int
    attempted_at: datetime
    status: str = "PROCESSING"  # PROCESSING, SENT, FAILED
    provider_message_id: str = ""
    error_code: str = ""
    error_message: str = ""
    response_reference: str = ""


class Technician(Base):
    """Technician/staff user model."""
    __tablename__ = "users"  # Using 'users' to avoid clash with Python 'user'

    id: int
    full_name: str
    email: str
    role: str = "TECHNICIAN_PAINTER"  # ADMIN_MANAGER, SERVICE_ADVISOR, TECHNICIAN_PAINTER, READ_ONLY
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
EOF
echo "Done"