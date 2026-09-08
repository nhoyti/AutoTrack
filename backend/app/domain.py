from enum import StrEnum


class StaffRole(StrEnum):
    ADMIN_MANAGER = "ADMIN_MANAGER"
    SERVICE_ADVISOR = "SERVICE_ADVISOR"
    TECHNICIAN_PAINTER = "TECHNICIAN_PAINTER"
    READ_ONLY = "READ_ONLY"


class CustomerStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    LEAD = "LEAD"


class PreferredContactMethod(StrEnum):
    SMS = "SMS"
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"
    PHONE = "PHONE"


class JobStatus(StrEnum):
    DRAFT = "DRAFT"
    INSPECTION = "INSPECTION"
    ESTIMATE = "ESTIMATE"
    CUSTOMER_APPROVAL = "CUSTOMER_APPROVAL"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    QUALITY_CHECK = "QUALITY_CHECK"
    READY_FOR_RELEASE = "READY_FOR_RELEASE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ReminderStage(StrEnum):
    THIRTY_DAYS = "30_DAYS"
    SEVEN_DAYS = "7_DAYS"
    DUE_TODAY = "DUE_TODAY"
    OVERDUE = "OVERDUE"


class IntakeStatus(StrEnum):
    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"


class InspectionStatus(StrEnum):
    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"


class ConcernSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
