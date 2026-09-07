# Autohaus Car Paint Shop & Preventive Maintenance System Architecture

## 1. Overview

This application is designed for a car paint/body repair shop with integrated customer, vehicle, inspection, paint-job, preventive maintenance service (PMS), and customer notification management.

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

Use an internal `vehicle_id` because a vehicle's plate can change.

---

# 4. Vehicle Intake & Inspection

Vehicle intake should capture both customer information and the condition of the vehicle when it arrives.

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
Customer Request:
Technician Notes:
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
description
recommended_action
customer_requested
created_at
```

## inspection_photos

```text
id
inspection_item_id
storage_path
photo_type
caption
created_at
```

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
technician_id
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

---

# 12. PMS Reminder Engine

The reminder engine should run as a background scheduled process.

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

---

# 14. Notification Database

## notifications

```text
id
customer_id
vehicle_id
maintenance_schedule_id

channel
notification_type

scheduled_at
sent_at

status
provider_message_id
error_message

created_at
```

### Channels

```text
SMS
EMAIL
MESSENGER
PUSH
```

### Notification Types

```text
PMS_30_DAY
PMS_7_DAY
PMS_DUE
PMS_OVERDUE
```

### Status

```text
PENDING
SENT
FAILED
CANCELLED
```

A notification audit trail is important for troubleshooting and customer-service history.

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

---

# 16. Vehicle History

The vehicle profile should be the single source of truth for the vehicle.

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

---

# 18. Dashboard

Management dashboard should expose operational and retention metrics.

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
Facebook Messenger integration
Push notifications
```

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

Recommended roles:

```text
ADMIN
MANAGER
SERVICE_ADVISOR
TECHNICIAN
PAINTER
CASHIER
VIEW_ONLY
```

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

## Phase 2 — Vehicle Inspection

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

- Digital inspection
- Damage areas
- Condition/severity
- Photo upload
- Technician notes

---

## Phase 3 — Paint Jobs

```text
Inspection
   ↓
Estimate
   ↓
Customer Approval
   ↓
Work Order
   ↓
Job Tracking
```

Build:

- Estimates
- Work orders
- Paint job items
- Job status
- Cost tracking

---

## Phase 4 — PMS

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

- PMS records
- Service history
- Odometer tracking
- Next service date
- Next service mileage
- Recommendations

---

## Phase 5 — Notifications

```text
Maintenance Schedule
        ↓
Reminder Engine
        ↓
SMS / Email / Messenger
```

Build:

- Notification preferences
- Reminder scheduler
- 30-day reminders
- 7-day reminders
- Due reminders
- Overdue reminders
- Notification logs

---

## Phase 6 — Analytics

Track:

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
