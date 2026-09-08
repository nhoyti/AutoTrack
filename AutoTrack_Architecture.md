# Autohaus Car Paint Shop & Preventive Maintenance System Architecture

## 1. Overview

This application is designed for a car paint/body repair shop with integrated customer, vehicle, inspection, paint-job, preventive maintenance service (PMS), and customer notification management.

The Single Page Application; MVP is an internal, staff-facing web application for one shop. Staff authenticate to the application and manage the vehicle lifecycle from intake through paint work, PMS history, and customer reminders. A customer portal, online booking, payments, inventory, AI recommendations, and multi-branch administration are outside the MVP.

### Initial Staff Roles

The MVP has four roles:

| Role                 | Responsibility                                                                                     |
| -------------------- | -------------------------------------------------------------------------------------------------- |
| `ADMIN_MANAGER`      | Manage staff access, shop configuration, and all operational records.                              |
| `SERVICE_ADVISOR`    | Manage customer and vehicle intake, inspections, estimates, approvals, and customer communication. |
| `TECHNICIAN_PAINTER` | Record inspection findings, photos, technician notes, paint work, and job progress.                |
| `READ_ONLY`          | View permitted customer, vehicle, job, service, and notification history without changing records. |

Authorization should be enforced by the API as well as the Angular interface. The role names above are the canonical MVP roles; more granular roles can be introduced later without changing the domain boundaries.

The core architectural principle is:

> **Customer → Vehicle → Inspection / Paint Jobs / PMS → Vehicle History → PMS Reminders → Customer Return**

The system should maintain a complete lifecycle history for every vehicle serviced by the shop.

---

## 2. High-Level Architecture

```text
                         ┌─────────────────────────┐
                         │       CUSTOMER          │
                         │                         │
                         │ Name                    │
                         │ Mobile                  │
                         │ Email                   │
                         │ Address                 │
                         │ Contact Preferences     │
                         └────────────┬────────────┘
                                      │
                                      │ 1:N
                                      ▼
                         ┌─────────────────────────┐
                         │        VEHICLE          │
                         │                         │
                         │ Plate Number            │
                         │ Make / Model            │
                         │ Year                    │
                         │ Color                   │
                         │ VIN / Chassis Number    │
                         │ Odometer                │
                         └────────────┬────────────┘
                                      │
                ┌─────────────────────┼─────────────────────┐
                │                     │                     │
                ▼                     ▼                     ▼
       ┌────────────────┐   ┌──────────────────┐   ┌──────────────────┐
       │ VEHICLE        │   │ PAINT / BODY     │   │ PMS / SERVICE    │
       │ INSPECTION     │   │ JOBS             │   │ HISTORY          │
       │                │   │                  │   │                  │
       │ Damage Areas   │   │ Estimate         │   │ Service          │
       │ Photos         │   │ Work Order       │   │ Odometer         │
       │ Concerns       │   │ Parts/Materials  │   │ Next PMS         │
       │ Condition      │   │ Status            │   │ Recommendations  │
       └────────────────┘   └──────────────────┘   └────────┬─────────┘
                                                            │
                                                            ▼
                                                   ┌──────────────────┐
                                                   │ PMS REMINDERS    │
                                                   │                  │
                                                   │ SMS              │
                                                   │ Email            │
                                                   │ Messenger        │
                                                   │ Push Notification│
                                                   └──────────────────┘
```

## 2.1 Aggregate Boundaries

Each aggregate has one owner and an internal identifier. Cross-domain references use IDs and do not allow one domain to mutate another domain's data directly.

| Aggregate    | Owns                                                                                                  | Does not own                                                                               |
| ------------ | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Customer     | Identity, contact details, contact preferences, and customer status.                                  | Vehicle history, inspection findings, jobs, or service records.                            |
| Vehicle      | Canonical vehicle identity and vehicle-level history links.                                           | Customer contact preferences or the internal details of inspections, jobs, or PMS records. |
| Inspection   | Intake snapshot, structured concern items, inspection notes, and photos.                              | Paint-job estimates or later edits to the vehicle record.                                  |
| Paint Job    | Estimates, work-order items, approval, job status, and status history.                                | The original inspection; it stores a snapshot/reference of the intake condition.           |
| PMS          | Completed service records, service items, parts, maintenance schedules, and schedule state history.   | Reminder delivery attempts or provider-specific message data.                              |
| Notification | Reminder business events, channel-specific delivery attempts, provider adapters, and delivery events. | Maintenance schedule rules or customer preference ownership.                               |

The vehicle profile is a read model assembled from these aggregates. It is the primary staff history view, but it is not a replacement for the owning aggregate records.

---

# 3. Core Modules

## 3.1 Customer Management

Stores customer information.

```text
customers
├── id
├── full_name
├── mobile_number
├── email
├── address
├── preferred_contact_method
├── notes
├── status
├── created_at
└── updated_at
```

A customer can own multiple vehicles.

Customer contact preferences belong to the Customer aggregate. Notification delivery must read those preferences and record the decision, but must not copy ownership of the preferences into PMS or Notification records.

---

## 3.2 Vehicle Management

The vehicle is the central entity for service history.

```text
vehicles
├── id
├── customer_id
├── plate_number
├── vin_chassis_number
├── make
├── model
├── variant
├── year
├── color
├── fuel_type
├── transmission
├── current_odometer
├── notes
├── created_at
└── updated_at
```

### Important Design Decision

Do **not** use the plate number as the primary key.

Use an immutable internal `vehicle_id` as the canonical identity because a vehicle's plate can change. The plate number is a normalized, searchable attribute and may be updated with an audit entry; it is never used as a foreign key.

VIN/chassis number should be searchable when present, but it is optional for intake and must not replace `vehicle_id`. If VIN uniqueness is enforced, it applies only to non-null normalized values.

### Vehicle Data-Quality Rules

- Every odometer reading stores its value, unit, recorded-at timestamp, and source record.
- A new odometer reading must not be lower than the vehicle's current reading. A correction requires an explicit audited action containing the previous value, corrected value, reason, actor, and timestamp.
- `current_odometer` is derived from the latest accepted reading and cannot be edited as an untracked free-form field.
- A vehicle may have multiple historical owners if ownership transfer is introduced. The current customer relationship must not erase prior ownership history; the transfer record should contain effective dates and an audit trail.
- Plate values are normalized for search, while preserving the entered/display form for staff.

---

# 4. Vehicle Intake & Inspection

Vehicle intake should capture both customer information and the condition of the vehicle when it arrives.

## 4.1 Staff Intake Workflow

The intake flow is completed by a service advisor or authorized staff member:

1. Search for an existing customer by name, mobile number, or email. Create the customer if no match exists, and confirm contact preferences before saving.
2. Search for an existing vehicle by plate, VIN/chassis number, or customer. Create the vehicle if no match exists, using the immutable vehicle ID as its identity.
3. Capture or confirm plate, make, model, year, color, VIN/chassis number, and the current odometer reading. Apply the vehicle odometer data-quality rules before accepting the reading.
4. Create an inspection linked to the vehicle, recording the intake date, accepted odometer reading, staff member, overall condition, and customer notes.
5. Add one or more structured concern items from the damage map or area list. Each item records the area, condition, severity, requested work, technician notes, recommended action, and photos.
6. Save the inspection as the intake baseline for any paint job created from it. Later corrections are audited and do not rewrite the job's original inspection snapshot.

The form should support draft saving so an interrupted intake can resume without creating duplicate customers, vehicles, or inspections. Submission requires the vehicle and inspection identity fields; concern items and photos may be added before the inspection is finalized.

## Customer Information

```text
Customer
────────────────────────
Name:
Mobile:
Email:

Vehicle
────────────────────────
Plate Number:
Make:
Model:
Year:
Color:

Odometer
────────────────────────
Current Reading:
```

## Areas of Concern

Use structured selections rather than relying only on free text.

```text
☐ Front Bumper
☐ Rear Bumper
☐ Hood
☐ Roof
☐ Left Front Fender
☐ Right Front Fender
☐ Left Rear Fender
☐ Right Rear Fender
☐ Left Front Door
☐ Right Front Door
☐ Left Rear Door
☐ Right Rear Door
☐ Trunk / Tailgate
☐ Side Mirror
☐ Headlight
☐ Taillight
☐ Windshield
☐ Wheels / Rims
☐ Interior
☐ Other
```

Each concern should support:

```text
Area:
Condition:
Severity:
Requested Work:
Technician Notes:
Recommended Action:
Photos:
```

### Suggested Condition Types

```text
SCRATCH
DENT
PAINT_FADE
PAINT_PEEL
CRACK
RUST
DISCOLORATION
CHIP
BROKEN
OTHER
```

### Suggested Severity

```text
MINOR
MODERATE
MAJOR
CRITICAL
```

---

# 5. Digital Vehicle Inspection

A vehicle diagram should be used to visually identify damaged or concerning areas.

```text
             FRONT
          ┌─────────┐
          │  HOOD   │
      ┌───┴─────────┴───┐
      │                  │
 LEFT │      ROOF        │ RIGHT
 SIDE │                  │ SIDE
      │                  │
      └───────┬──────────┘
              │
             REAR
```

Technicians should be able to select an area and attach:

- Condition
- Severity
- Notes
- Photos
- Recommended action

This creates structured inspection data instead of unstructured notes.

---

# 6. Inspection Database

## vehicle_inspections

```text
id
vehicle_id
inspection_date
odometer_reading
fuel_level
overall_condition
customer_notes
technician_notes
created_by
created_at
updated_at
```

## inspection_items

```text
id
inspection_id
vehicle_area
condition_type
severity
requested_work
technician_notes
recommended_action
created_at
```

## inspection_photos

```text
id
inspection_item_id
storage_path
photo_type
caption
uploaded_by
created_at
```

Photos are stored in object storage, while the database stores the inspection-item link, storage key, content type, dimensions, upload actor, and timestamps. Downloads must use authorized, time-limited URLs rather than public storage paths.

---

# 7. Paint / Body Repair Job Management

Recommended workflow:

```text
DRAFT
  ↓
INSPECTION
  ↓
ESTIMATE
  ↓
CUSTOMER APPROVAL
  ↓
SCHEDULED
  ↓
IN PROGRESS
  ↓
QUALITY CHECK
  ↓
READY FOR RELEASE
  ↓
COMPLETED
```

Alternative terminal state:

```text
CANCELLED
```

## 7.1 Paint Job Workflow Rules

- A paint job is created from one inspection and keeps `inspection_id` as a required reference.
- Creating a job copies the relevant inspection concern items into a job snapshot, including area, condition, severity, requested work, recommended action, and photo references as they existed at intake.
- Editing the inspection after job creation does not change the job snapshot. Any later finding is added through a new inspection or an explicitly audited job update.
- Status changes are append-only in `paint_job_status_history`, recording the prior status, new status, actor, timestamp, and reason where applicable.
- Only an authorized service advisor or admin/manager may approve an estimate, and only an authorized technician/painter or admin/manager may move a job through production and quality check.
- `COMPLETED` and `CANCELLED` are terminal states. A cancelled job cannot resume; a new job must be created if work is reopened.

## paint_jobs

```text
id
vehicle_id
inspection_id
job_number
job_type
description
status
estimated_cost
approved_cost
actual_cost
scheduled_start
scheduled_end
actual_completion_date
customer_notes
technician_notes
created_at
updated_at
```

## paint_job_items

```text
id
paint_job_id
vehicle_area
service_type
description
labor_cost
material_cost
quantity
total_cost
status
```

Examples of services:

```text
SANDING
BODY_REPAIR
DENT_REPAIR
PRIMER
PAINT
CLEAR_COAT
POLISHING
BUFFING
PANEL_REPLACEMENT
PANEL_ALIGNMENT
RUST_REPAIR
```

---

# 8. Preventive Maintenance Service (PMS)

PMS is a separate service domain but remains linked to the vehicle.

PMS service records are created for work performed on a vehicle. A record may remain a draft while staff enter service items, parts, costs, recommendations, and the odometer reading. Only completion creates or updates a maintenance schedule. A body/paint job may appear in vehicle history, but it does not create a PMS schedule unless it contains an explicit PMS service item.

Example:

```text
Toyota Fortuner
Plate: ABC 1234
Current Odometer: 52,430 km

SERVICE HISTORY

Date          Odometer     Service
────────────────────────────────────────
Jan 10 2025   30,000 km    PMS
Jul 15 2025   35,000 km    Oil Change
Jan 20 2026   40,000 km    PMS
Jul 20 2026   45,000 km    Oil Change
Sep 08 2026   52,430 km    Body Repair
```

---

# 9. Service Records

## service_records

```text
id
vehicle_id
service_date
odometer_reading
service_type
description
completed_at
completed_by
status
labor_cost
parts_cost
total_cost
recommendations
created_at
updated_at
```

## service_items

```text
id
service_record_id
service_category
description
status
cost
next_due_odometer
next_due_date
rule_type
```

## service_parts

```text
id
service_record_id
part_name
part_number
quantity
unit_cost
total_cost
```

### PMS Record Rules

- `vehicle_id`, `service_date`, `service_type`, and `status` are required. `odometer_reading` is required when the service includes an odometer-based schedule and must pass the vehicle regression rule.
- Costs are stored as non-negative decimal amounts with an explicit currency. `total_cost` is calculated from labor, parts, and service items rather than trusted from client input.
- A service record can transition from `DRAFT` to `COMPLETED` or `CANCELLED`. Completion records `completed_at` and `completed_by` and is append-only from the audit perspective.
- Completing a record is one transaction: validate the record, accept the odometer reading, create its schedules, and supersede any replaced active schedules. A failure rolls back the whole operation.
- Updating a completed record is prohibited for operational fields. Corrections use an audited adjustment or a replacement record and never delete the original history.

---

# 10. PMS Service Types

Recommended initial service categories:

```text
PMS
OIL_CHANGE
BRAKE_SERVICE
TRANSMISSION_SERVICE
COOLING_SYSTEM
BATTERY
TIRE_ROTATION
WHEEL_ALIGNMENT
AIR_FILTER
CABIN_FILTER
SPARK_PLUG
FUEL_FILTER
BELT_INSPECTION
SUSPENSION
AIR_CONDITIONING
GENERAL_INSPECTION
OTHER
```

---

# 11. Maintenance Schedule

Every completed PMS/service record can optionally generate a future maintenance schedule.

Example:

```text
Last PMS
────────────────
Date: Sep 8, 2026
Odometer: 50,000 km

Next PMS
────────────────
Date: Mar 8, 2027
Odometer: 60,000 km

Rule:
Whichever comes first
```

## maintenance_schedules

```text
id
vehicle_id
service_record_id
maintenance_type
due_date
due_odometer
interval_months
interval_km
rule_type
status
source_service_item_id
completed_at
completed_by
superseded_by_schedule_id
notes
created_at
updated_at
```

Possible `rule_type` values:

```text
DATE_ONLY
ODOMETER_ONLY
WHICHEVER_COMES_FIRST
WHICHEVER_COMES_LAST
```

### Schedule Evaluation

Schedule evaluation uses the shop timezone and a supplied evaluation instant; it must not depend on the worker machine's local timezone or current clock during tests. Date comparisons use local calendar dates, while odometer comparisons use accepted readings in the vehicle's configured unit.

For a schedule with due date `D` and due odometer `O`, where the current date is `d` and current odometer is `o`:

| Rule                    | Due when              |
| ----------------------- | --------------------- |
| `DATE_ONLY`             | `d >= D`              |
| `ODOMETER_ONLY`         | `o >= O`              |
| `WHICHEVER_COMES_FIRST` | `d >= D` or `o >= O`  |
| `WHICHEVER_COMES_LAST`  | `d >= D` and `o >= O` |

An incomplete schedule is `PLANNED` before its due condition, `DUE` on the first due date or odometer threshold, and `OVERDUE` after the due date or when the odometer has passed the applicable threshold. The evaluator returns the same result for the same schedule, vehicle readings, timezone, and evaluation instant.

### Schedule States and Transitions

```text
PLANNED ──► DUE ──► OVERDUE
   │          │         │
   ├──────────┴─────────┴──► COMPLETED
   └────────────────────────► SKIPPED
```

`CANCELLED` may be used instead of `SKIPPED` when staff intentionally remove a future schedule. State changes record actor, timestamp, previous state, new state, and reason. Completing a later service marks the replaced schedule `COMPLETED` or `SKIPPED` with a link to the new source record; the old schedule and its state history remain queryable.

Only one active schedule for the same vehicle, maintenance type, and source service chain may be current at a time. A schedule must retain its source service record and, when applicable, source service item.

---

# 12. PMS Reminder Engine

The reminder engine should run as a background scheduled process.

The reminder is the business event that a maintenance schedule has entered a reminder stage. A notification is a channel-specific delivery attempt for that reminder. The scheduler creates reminders; the notification dispatcher delivers them. Neither process may create duplicate records when a worker is retried.

```text
                 ┌──────────────────────┐
                 │ PMS REMINDER ENGINE   │
                 └──────────┬───────────┘
                            │
                     Daily scheduler
                            │
                            ▼
                 ┌──────────────────────┐
                 │ Find upcoming PMS    │
                 └──────────┬───────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
          30 DAYS         7 DAYS         DUE
              │             │             │
              ▼             ▼             ▼
             SMS         SMS/Email     SMS/Email
```

Recommended reminder stages:

```text
30 DAYS BEFORE
7 DAYS BEFORE
DUE TODAY
OVERDUE
```

### Reminder Generation

On each run, a timezone-aware worker:

1. Finds active schedules whose evaluated state and due date/odometer place them in a configured stage.
2. Creates at most one reminder for each `schedule_id + stage` key. A schedule entering `OVERDUE` creates a new stage reminder, while rerunning the same stage is a no-op.
3. Reads the customer's current consent, enabled channels, preferred channel, quiet hours, and timezone.
4. Creates one pending notification delivery per eligible channel using the unique key `reminder_id + channel`.
5. Hands pending deliveries to the dispatcher, which performs provider calls and records every attempt and provider event.

The scheduler and dispatcher are independently retryable. A scheduler crash can safely rerun the same window, and a dispatcher crash can safely retry a pending delivery without creating a second business reminder. Consent is checked immediately before dispatch as well as during generation; an opt-out cancels unsent deliveries.

Reminder stages are `30_DAYS`, `7_DAYS`, `DUE_TODAY`, and `OVERDUE`. A stage is generated only once per schedule, even if the worker runs multiple times during that stage. Reminder generation is skipped for completed, skipped, or cancelled schedules.

---

# 13. Notification Architecture

Notification logic should be separated from the PMS domain.

```text
PMS RECORD CREATED
        │
        ▼
Calculate Next Service
        │
        ▼
Create Maintenance Schedule
        │
        ▼
Reminder Scheduler
        │
        ▼
Create Notification
        │
        ├──► SMS Provider
        ├──► Email Provider
        ├──► Messenger
        └──► Push Notification
```

This allows notification providers to be added or replaced without modifying PMS logic.

### Provider Adapter Contract

Each provider adapter implements the same interface:

```text
send(message, recipient, metadata) ->
   { provider_message_id, accepted_at }
```

The adapter must not decide business eligibility. The dispatcher validates consent, channel, recipient, quiet hours, and cancellation state before calling it. Provider responses and webhooks are normalized into delivery events with the delivery ID, provider message ID, event type, event time, and raw response reference.

Initial channels are `SMS`, `EMAIL`, and a provider-agnostic `MESSENGER_WHATSAPP` integration. The adapter boundary hides whether the configured chat provider is Messenger or WhatsApp; templates, consent requirements, and webhook details remain provider-specific.

Delivery attempts use exponential backoff for transient failures and stop after a configured maximum. Permanent failures become `FAILED` immediately. A schedule completion cancels pending deliveries for its unsent reminders; sent messages remain part of the audit history.

---

# 14. Notification Database

## notifications

```text
id
customer_id
vehicle_id
maintenance_schedule_id
reminder_id

channel
stage

scheduled_at
sent_at
attempt_count
next_attempt_at

status
provider_message_id
error_message

created_at
```

### Channels

```text
SMS
EMAIL
MESSENGER_WHATSAPP
```

### Reminder Stages

```text
30_DAYS
7_DAYS
DUE_TODAY
OVERDUE
```

### Status

```text
PENDING
PROCESSING
SENT
FAILED
CANCELLED
```

A notification audit trail is important for troubleshooting and customer-service history.

## maintenance_reminders

```text
id
maintenance_schedule_id
customer_id
vehicle_id
stage
scheduled_for
generated_at
status
cancelled_at
cancelled_reason
created_at
updated_at
```

`maintenance_reminders` stores the business event. `notifications` stores one delivery record per channel, and `notification_attempts` stores each provider call and result.

## notification_attempts

```text
id
notification_id
attempt_number
attempted_at
status
provider_message_id
error_code
error_message
response_reference
```

Required database constraints and indexes:

- Unique `maintenance_reminders(maintenance_schedule_id, stage)` for scheduler idempotency.
- Unique `notifications(reminder_id, channel)` for channel delivery idempotency.
- Index active schedules by `(status, due_date, due_odometer)` and pending notifications by `(status, next_attempt_at)`.
- Index customer contact fields and notification delivery status for staff search and audit views.
- Foreign keys from reminders and notifications to their source schedule, customer, vehicle, and reminder are required; historical delivery records are not hard-deleted.

---

# 15. Customer Notification Preferences

Customers should control how they receive reminders.

```text
customer_notification_preferences

id
customer_id
sms_enabled
email_enabled
messenger_enabled
push_enabled
pms_reminders_enabled
marketing_enabled
created_at
updated_at
```

The system should respect these preferences before sending notifications.

Preferences are evaluated per customer at dispatch time. `pms_reminders_enabled` is the master opt-in; a channel flag must also be enabled. The preferred channel is attempted first, with fallback channels allowed only when the customer's policy permits them. Every suppressed, cancelled, or skipped delivery records a reason.

Each customer preference record should also include `timezone`, `quiet_hours_start`, and `quiet_hours_end`. Scheduled times are stored in UTC and displayed in the customer's timezone. A delivery inside quiet hours is deferred to the next permitted local time, not marked failed.

---

# 16. Vehicle History

The vehicle profile should be the single source of truth for the vehicle.

The profile is a read model assembled from the Customer, Vehicle, Inspection, Paint Job, PMS, and Notification domains. It must preserve the source record IDs and timestamps so staff can navigate from a summary row to the owning record without creating a second editable copy.

```text
TOYOTA FORTUNER
ABC 1234

52,430 KM
────────────────────────────────────────

[Overview]
[Inspection]
[Paint Jobs]
[PMS History]
[Photos]
[Documents]

OWNER
Juan Dela Cruz

CURRENT CONCERNS
⚠ Front bumper scratches
⚠ Paint fading - roof
⚠ Minor dent - rear door

NEXT PMS
March 2027 / 60,000 km

SERVICE HISTORY
✓ Jan 2026 - PMS
✓ Jul 2026 - Oil Change
✓ Sep 2026 - Paint Repair
```

---

# 17. Customer Profile

```text
CUSTOMER
Juan Dela Cruz
0917 XXX XXXX

VEHICLES

Toyota Fortuner
ABC 1234
52,430 km

Honda Civic
XYZ 5678
38,200 km

RECENT ACTIVITY

Sep 08 2026 - Paint Repair
Sep 08 2026 - Vehicle Inspection
Jul 20 2026 - PMS

UPCOMING

Toyota Fortuner
PMS due March 2027 / 60,000 km
```

### Vehicle Profile Sections

- **Overview:** current identity, customer relationship, current odometer, active job, and next maintenance.
- **Inspections:** finalized and draft inspections, concern counts, condition/severity summary, and inspection dates.
- **Paint Jobs:** active and completed jobs, estimate/approval amounts, current status, and status history.
- **PMS History:** completed service records, items, parts, costs, recommendations, and source schedules.
- **Photos:** authorized inspection and job photos grouped by source item and date.
- **Documents:** metadata and authorized links for estimates, approvals, and work-order documents.
- **Next PMS:** active schedules with due date, due odometer, rule, evaluated state, and reminder delivery summary.

The profile defaults to the most recent operational activity, but history remains filterable by date, type, status, and staff member. Customer contact data is masked for roles that do not need full contact access.

---

# 18. Dashboard

Management dashboard should expose operational and retention metrics.

The MVP dashboard is an operational view, not an analytics warehouse. Every count is scoped to the single shop and evaluated against an explicit timezone-aware reporting date.

```text
┌────────────┐ ┌────────────┐ ┌────────────┐
│  TODAY     │ │ IN PROGRESS│ │ PMS DUE    │
│     8      │ │     5      │ │    23      │
│ Vehicles   │ │ Jobs       │ │ Customers  │
└────────────┘ └────────────┘ └────────────┘

┌─────────────────────────────────────────────┐
│ TODAY'S VEHICLES                            │
├──────────┬────────────┬─────────────────────┤
│ Plate    │ Customer   │ Status              │
├──────────┼────────────┼─────────────────────┤
│ ABC1234  │ Juan       │ Painting            │
│ XYZ5678  │ Pedro      │ Inspection          │
│ DEF9876  │ Maria      │ Ready               │
└──────────┴────────────┴─────────────────────┘

┌─────────────────────────────────────────────┐
│ UPCOMING PMS                                │
├──────────┬────────────┬─────────────────────┤
│ Customer │ Vehicle    │ Due                 │
├──────────┼────────────┼─────────────────────┤
│ Juan     │ Fortuner   │ 7 days              │
│ Pedro    │ Civic      │ 14 days             │
└──────────┴────────────┴─────────────────────┘
```

### Dashboard Queries

- **Today's jobs:** paint jobs with work scheduled or status activity on the reporting date.
- **Active work:** jobs in `SCHEDULED`, `IN_PROGRESS`, or `QUALITY_CHECK`.
- **Upcoming PMS:** active schedules due within the configured forward window, ordered by effective due date.
- **Overdue PMS:** schedules evaluated as `OVERDUE`, grouped by customer and vehicle.
- **Failed notifications:** deliveries in `FAILED` state or exhausted retry attempts, with the latest failure reason.

Dashboard queries return aggregate counts and paginated rows from source read models. They must not trigger reminder generation, provider calls, or status changes.

---

# 19. Recommended Technology Stack

For an Autohaus implementation:

```text
Frontend
──────────────
Angular
TypeScript
Angular Material
SCSS

Backend
──────────────
Python
FastAPI
Pydantic
SQLAlchemy

Database
──────────────
PostgreSQL
Supabase

File Storage
──────────────
Supabase Storage

Background Jobs
──────────────
Scheduled worker / cron
Redis + worker if scaling requires it

Authentication
──────────────
Supabase Auth or application-managed authentication

Notifications
──────────────
SMS provider
Email provider
Messenger/WhatsApp-compatible provider adapter
```

### Delivery Baseline

The MVP is deployed for one shop with one operational timezone and one staff organization. A future `branch_id` may be added to top-level records, but tenancy, branch administration, cross-branch reporting, and branch-level provider configuration are explicitly deferred. The deployment must still isolate configuration and secrets by environment and support database backups, object-storage retention, and worker health monitoring.

---

# 20. Angular Feature Architecture

Organize Angular by business domain.

```text
src/app/

├── core/
│   ├── auth/
│   ├── api/
│   ├── guards/
│   ├── interceptors/
│   └── notifications/
│
├── shared/
│   ├── components/
│   ├── directives/
│   ├── pipes/
│   └── models/
│
├── features/
│
│   ├── customers/
│   │   ├── customer-list/
│   │   ├── customer-detail/
│   │   └── customer-form/
│   │
│   ├── vehicles/
│   │   ├── vehicle-list/
│   │   ├── vehicle-detail/
│   │   └── vehicle-form/
│   │
│   ├── inspections/
│   │   ├── inspection-form/
│   │   ├── damage-map/
│   │   └── photo-gallery/
│   │
│   ├── paint-jobs/
│   │   ├── job-list/
│   │   ├── job-detail/
│   │   ├── estimate/
│   │   └── work-order/
│   │
│   ├── maintenance/
│   │   ├── service-history/
│   │   ├── service-record/
│   │   ├── maintenance-schedule/
│   │   └── reminders/
│   │
│   └── dashboard/
│
└── app.routes.ts
```

### Phase 2 Screens

The first usable staff workflow consists of these screens:

```text
Customer Search / Create
   ↓
Vehicle Search / Create
   ↓
Vehicle Profile
   ↓
Inspection Form + Damage Map + Photo Upload
   ↓
Paint Estimate / Work Order
   ↓
Job Status History
```

The vehicle profile links back to the active inspection and paint jobs without duplicating their editable data. The inspection form must work on desktop and tablet-sized screens, preserve draft state, and show upload progress and failed-photo retry state.

---

# 21. API Architecture

Recommended FastAPI routes:

```text
/api

├── /customers
│   ├── GET
│   ├── POST
│   ├── PUT
│   └── DELETE
│
├── /vehicles
│   ├── GET
│   ├── POST
│   ├── PUT
│   └── DELETE
│
├── /inspections
│   ├── POST
│   ├── GET
│   ├── PUT
│   └── /photos
│
├── /paint-jobs
│   ├── POST
│   ├── GET
│   ├── PUT
│   └── /status
│
├── /services
│   ├── POST
│   ├── GET
│   └── /history
│
├── /maintenance
│   ├── /schedules
│   ├── /upcoming
│   ├── /due
│   └── /overdue
│
└── /notifications
    ├── /send
    ├── /history
    └── /preferences
```

### Phase 2 API Contracts

The API should expose these resource shapes and behaviors. Response examples are illustrative and omit transport metadata.

```text
GET  /api/customers?query={name|mobile|email}
   -> { items: [{ id, full_name, mobile_number, email, vehicle_count }] }

GET  /api/vehicles?query={plate|vin|customer_id}
   -> { items: [{ id, customer_id, plate_number, make, model, year,
            color, vin_chassis_number, current_odometer }] }

GET  /api/vehicles/{vehicle_id}/profile
   -> { vehicle, customer, inspections, paint_jobs, service_summary,
      next_maintenance }

POST /api/vehicles/{vehicle_id}/inspections
   body: { inspection_date, odometer_reading, overall_condition,
         customer_notes, items: [{ vehicle_area, condition_type,
         severity, requested_work, technician_notes,
         recommended_action }] }

POST /api/inspections/{inspection_id}/photos
   multipart upload; returns { id, inspection_item_id, storage_key,
                     content_type, uploaded_at }

POST /api/paint-jobs
   body: { vehicle_id, inspection_id, job_type, description, items }
   -> creates a job with an inspection snapshot

POST /api/paint-jobs/{job_id}/estimate/approve
   body: { approved_cost, approved_by }

POST /api/paint-jobs/{job_id}/status
   body: { status, reason }
   -> appends status history and returns the current job

POST /api/vehicles/{vehicle_id}/services
   body: { service_date, odometer_reading, service_type, description,
         items, parts, recommendations }
   -> creates a DRAFT service record

POST /api/services/{service_id}/complete
   body: { completed_at, schedules: [{ maintenance_type, due_date,
         due_odometer, interval_months, interval_km, rule_type }] }
   -> completes the service and creates/supersedes schedules atomically

GET  /api/vehicles/{vehicle_id}/services
   -> returns service records, items, parts, and completion history

GET  /api/vehicles/{vehicle_id}/maintenance/schedules?status={status}
   -> returns schedules evaluated using the shop timezone and supplied clock

POST /api/maintenance/schedules/{schedule_id}/status
   body: { status, reason }
   -> applies an allowed transition and appends state history

GET  /api/vehicles/{vehicle_id}/maintenance/reminders
   -> returns reminder events and delivery summaries

POST /api/maintenance/reminders/run
   body: { evaluated_at }
   -> idempotently generates due reminder stages for active schedules

GET  /api/notifications?status={status}&customer_id={id}
   -> returns channel deliveries and latest attempt status

POST /api/notifications/{notification_id}/cancel
   body: { reason }
   -> cancels an unsent delivery and records the actor/reason

POST /api/notifications/providers/{channel}/events
   body: { provider_message_id, event_type, occurred_at, payload }
   -> records a normalized provider delivery event
```

All write endpoints return validation errors without partial aggregate updates. The API must enforce the role permissions, odometer rules, allowed status transitions, inspection-to-vehicle consistency, schedule rule requirements, photo authorization, notification consent, and delivery ownership independently of the client. Schedule and reminder evaluation accept an explicit evaluation instant in application services and tests; production workers provide the current instant.

---

# 22. Database Relationship Model

```text
customers
    │
    │ 1:N
    ▼
vehicles
    │
    ├────────── 1:N ──────────► vehicle_inspections
    │                              │
    │                              ├── inspection_items
    │                              └── inspection_photos
    │
    ├────────── 1:N ──────────► paint_jobs
    │                              │
    │                              └── paint_job_items
    │
    └────────── 1:N ──────────► service_records
                                   │
                                   ├── service_items
                                   └── service_parts

service_records
        │
        ▼
maintenance_schedules
        │
        ▼
maintenance_reminders / notifications
        │
        ▼
customer
```

---

# 23. Suggested Complete Database

```text
customers
vehicles

vehicle_inspections
inspection_items
inspection_photos

paint_jobs
paint_job_items
paint_job_status_history

service_records
service_items
service_parts

maintenance_schedules
maintenance_reminders

customer_notification_preferences
notifications
notification_logs

technicians
users
```

---

# 24. Security & Audit

The system should include:

- Authentication
- Role-based authorization
- Audit logs
- Soft deletion where appropriate
- Input validation
- API authorization
- Secure file uploads
- Storage access controls
- Notification logs
- Work-order status history

### Authorization Rules

- Authentication is required for every staff route and API endpoint except the authentication callback and provider webhooks.
- API authorization is the source of truth; Angular guards only improve navigation and must not be treated as security controls.
- `ADMIN_MANAGER` can manage users, configuration, records, audit views, and corrections.
- `SERVICE_ADVISOR` can manage customer/vehicle intake, inspections, estimates, approvals, schedules, and notification preferences within operational policy.
- `TECHNICIAN_PAINTER` can manage assigned inspection findings, photos, job work, and production status, but cannot approve estimates or access unnecessary customer contact details.
- `READ_ONLY` can view permitted operational history and dashboard data but cannot create, update, upload, approve, cancel, or dispatch records.
- Sensitive customer contact fields, provider credentials, signed photo URLs, and audit records require least-privilege access.

### Secure Uploads and Data Handling

- Accept only allowlisted image/document MIME types and enforce size and dimension limits.
- Generate storage keys server-side; never use a user-provided filename as a storage path.
- Scan or validate uploaded content before making it available to staff.
- Store private objects and issue short-lived, record-authorized signed URLs.
- Validate that every photo's inspection item, vehicle, and requesting staff member belong to the same authorized scope.
- Soft-delete business records only where history and foreign-key integrity permit it; preserve audit and delivery records.

### Audit Log

Every audit entry stores actor, action, entity type, entity ID, occurred-at timestamp, request/correlation ID, and before/after values or a structured change summary. Audit records are append-only to application roles. At minimum, log authentication and authorization failures, customer contact changes, vehicle identity and odometer corrections, uploads/deletions, estimate approvals, job and schedule transitions, preference changes, reminder suppression, notification attempts, provider events, and administrative changes.

Recommended roles:

```text
ADMIN_MANAGER
SERVICE_ADVISOR
TECHNICIAN_PAINTER
READ_ONLY
```

The following actions require audit entries: vehicle identity changes, odometer corrections, ownership transfers, inspection edits after job creation, estimate approval, paint-job status changes, PMS schedule status changes, notification cancellation, and changes to customer contact preferences.

---

# 25. Future PMS Intelligence

Once sufficient service history exists, the system can estimate future service dates.

Example:

```text
Current Odometer:
52,430 km

Historical Average:
1,200 km/month

Last PMS:
50,000 km

Next PMS:
60,000 km

Estimated Date:
March 2027
```

The system can eventually provide:

```text
SERVICE RECOMMENDATIONS

⚠ Engine oil service approaching
⚠ Brake inspection recommended
⚠ Tire rotation due
⚠ Battery inspection recommended
✓ Air filter recently replaced
```

This can evolve into a vehicle-maintenance recommendation engine.

---

# 26. MVP Development Roadmap

## Phase 1 — Customer & Vehicle

```text
Customer
   ↓
Vehicle
   ↓
Vehicle Profile
```

Build:

- Customer CRUD
- Vehicle CRUD
- Customer-to-vehicle relationship
- Search
- Vehicle profile

---

## Phase 2 — Intake, Inspection & Paint Jobs

```text
Vehicle
   ↓
Inspection
   ↓
Areas of Concern
   ↓
Photos
```

Build:

- Customer and vehicle search/create intake
- Plate, VIN, vehicle details, and odometer capture
- Digital inspection with draft and finalize states
- Damage map and structured concern areas
- Condition, severity, requested work, technician notes, and recommended action
- Authorized photo upload with inspection-item links
- Paint estimate/work order creation from an inspection snapshot
- Paint-job status history through completion or cancellation
- Estimates
- Work orders
- Paint job items
- Job status
- Cost tracking

---

## Phase 3 — PMS and Maintenance

```text
Vehicle
   ↓
Service Record
   ↓
Next PMS
   ↓
Maintenance Schedule
```

Build:

- Draft and completed PMS service records
- Service items, parts, costs, and recommendations
- Odometer validation and audit history
- Schedule creation on service completion
- Date-only, odometer-only, whichever-first, and whichever-last rules
- Deterministic, timezone-aware schedule evaluation
- Planned, due, overdue, completed, skipped, and cancelled schedule states
- Schedule supersession without deleting history

---

## Phase 4 — Notifications

```text
Maintenance Schedule
        ↓
Reminder Engine
        ↓
SMS / Email / Messenger
```

Build:

- Customer notification preferences, timezone, and quiet hours
- Separate reminder business events from channel deliveries
- Idempotent 30-day, 7-day, due-today, and overdue generation
- SMS, email, and Messenger/WhatsApp-compatible provider adapters
- Delivery attempts, provider IDs, normalized events, and audit logs
- Consent checks before generation and dispatch
- Retry/backoff for transient provider failures
- Cancellation of unsent deliveries when schedules are completed
- Staff views for failed, cancelled, and pending notifications

---

## Phase 5 — Security, Reporting and Delivery

Build:

- API-enforced authentication and role authorization
- Secure private photo/document storage and signed URLs
- Append-only audit logs and correction workflows
- Vehicle profile read model with the defined history sections
- Dashboard views for today's jobs, active work, upcoming/overdue PMS, and failed notifications
- Single-shop deployment, backup, retention, and worker health checks

Defer the following analytics until the operational foundation is stable:

```text
Customer Retention
PMS Conversion
Repeat Customers
Paint Jobs
Service Revenue
PMS Revenue
Upcoming PMS
Overdue PMS
Vehicle Service Frequency
Most Common Damage Areas
```

---

# 27. Long-Term Product Vision

The application should eventually become an:

## Autohaus Vehicle Lifecycle Platform

```text
                    CUSTOMER
                       │
                       ▼
                    VEHICLE
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      INSPECTION     PAINT         PMS
          │            │            │
          ▼            ▼            ▼
       CONCERNS      REPAIR       SERVICE
          │            │            │
          └────────────┼────────────┘
                       ▼
                 VEHICLE HISTORY
                       │
                       ▼
               MAINTENANCE ENGINE
                       │
                       ▼
                   REMINDERS
                       │
                       ▼
                   CUSTOMER
                       │
                       ▼
                 RETURN VISIT
```

The most important business loop is:

**Customer → Service → PMS Reminder → Customer Return → New Service**

This turns the application from a simple paint-shop management system into a customer-retention and vehicle-lifecycle platform.

---

# 28. Recommended Architecture Principle

Keep these domains separate:

```text
CUSTOMER DOMAIN
VEHICLE DOMAIN
INSPECTION DOMAIN
PAINT JOB DOMAIN
PMS DOMAIN
NOTIFICATION DOMAIN
AUTHENTICATION DOMAIN
REPORTING DOMAIN
```

They should communicate through well-defined APIs/events rather than tightly coupled components.

This will make it easier to add future capabilities such as:

- Online booking
- Customer portal
- Mobile technician app
- Digital estimates
- Digital signatures
- Payment integration
- Parts inventory
- Accounting
- Loyalty programs
- Automated marketing
- AI-assisted damage assessment
- AI-generated service recommendations
- Fleet customer management
- Multi-branch Autohaus support
