# AutoTrack MVP Sprint Plan

## Product Scope

AutoTrack is an internal staff application for a single autohaus/body-repair shop. The MVP supports the operational lifecycle:

> Customer -> Vehicle -> Inspection -> Job / Service -> Reminder -> Notification -> Dashboard

### MVP Roles

- `ADMIN_MANAGER`
- `SERVICE_ADVISOR`
- `TECHNICIAN_PAINTER`
- `READ_ONLY`

### MVP Technology Direction

- Frontend: Angular, TypeScript, Angular Material, SCSS
- Backend: Python, FastAPI, Pydantic, SQLAlchemy
- Database: PostgreSQL / Supabase
- Storage: Private object storage, such as Supabase Storage
- Background work: Scheduled worker or cron
- Notifications: SMS, email, and Messenger/WhatsApp-compatible provider adapters

Customer portals, online booking, payments, inventory, AI recommendations, and multi-branch administration are deferred.

## Delivery Cadence

The recommended cadence is eight two-week sprints, preceded by a short planning and decision sprint. Each sprint must end with a demonstrable increment and verified acceptance criteria.

## Sprint 0: Decisions and Delivery Foundation

**Duration:** 1 week

### Goals

- Confirm authentication approach, notification providers, shop timezone, currency, odometer units, retention policy, and backup targets.
- Create the application structure for Angular, FastAPI, database migrations, and background workers.
- Set up local development, environment configuration, CI, formatting, linting, and testing.
- Define API error responses, pagination, filtering, timestamp rules, audit events, and frontend feature boundaries.

### Exit Criteria

A new developer can run the frontend, API, database, and worker locally, and CI runs the basic quality checks.

## Sprint 1: Authentication and Core Foundations

### Goals

- Implement staff authentication and session management.
- Add API-enforced role authorization.
- Add frontend route guards for navigation.
- Create users, audit events, shop configuration, timestamps, and common database conventions.
- Establish API error handling and permission testing.

### Exit Criteria

Staff can sign in, access permitted areas, and unauthorized API mutations are rejected even when the UI is bypassed.

## Sprint 2: Customers and Vehicles

### Goals

- Implement Customer and Vehicle records.
- Add search by customer name, mobile number, email, plate number, and VIN/chassis number.
- Enforce immutable internal `vehicle_id` values.
- Treat plate numbers as mutable, normalized search attributes rather than foreign keys.
- Add append-only odometer readings.
- Add audited odometer correction workflows.
- Build customer and vehicle list/detail screens.

### Exit Criteria

Staff can create or find a customer and vehicle, record a valid odometer reading, and view the vehicle history shell. Invalid odometer regressions are rejected.

## Sprint 3: Intake and Digital Inspections

### Goals

- Implement draft and resumable intake workflows.
- Add inspection records and structured concern items.
- Support vehicle area, condition, severity, requested work, technician notes, and recommendations.
- Add private photo storage with server-generated keys.
- Validate MIME type, file size, dimensions, and access permissions.
- Add signed or time-limited photo URLs.
- Show upload progress, retry, and failure states.

### Exit Criteria

Staff can resume an intake without creating duplicates, complete a structured inspection, and securely attach and view photos.

## Sprint 4: Paint and Body Repair Jobs

### Goals

- Create paint/body jobs from inspections.
- Snapshot inspection concerns and photo references when a job is created.
- Add job items, estimates, approvals, costs, scheduling, and notes.
- Implement the job workflow:

```text
DRAFT
  -> INSPECTION
  -> ESTIMATE
  -> CUSTOMER_APPROVAL
  -> SCHEDULED
  -> IN_PROGRESS
  -> QUALITY_CHECK
  -> READY_FOR_RELEASE
  -> COMPLETED
```

- Support `CANCELLED` as a terminal state.
- Record append-only job status history.
- Enforce role-based transition permissions.
- Add approval and status audit events.

### Exit Criteria

A repair job can move from intake through completion with correct role restrictions, status history, and an inspection snapshot that remains unchanged when the original inspection is edited.

## Sprint 5: PMS and Maintenance Schedules

### Goals

- Implement service records, service items, parts, labor, costs, and recommendations.
- Support draft, completed, and cancelled service records.
- Make completed records operationally immutable.
- Implement transactional PMS completion:
  1. Validate the service record.
  2. Accept the odometer reading.
  3. Create or supersede maintenance schedules.
  4. Commit all changes atomically.
- Implement schedule rules:
  - `DATE_ONLY`
  - `ODOMETER_ONLY`
  - `WHICHEVER_COMES_FIRST`
  - `WHICHEVER_COMES_LAST`
- Add deterministic schedule evaluation.
- Add schedule state history.

### Exit Criteria

Completing a PMS record creates the correct active schedule exactly once. A failed transaction rolls back the odometer and schedule changes together.

## Sprint 6: Reminders and Notifications

### Goals

- Build the scheduled reminder worker.
- Support reminder stages:
  - `30_DAYS`
  - `7_DAYS`
  - `DUE_TODAY`
  - `OVERDUE`
- Make reminder generation idempotent.
- Implement notification delivery records and attempt history.
- Create provider adapters for SMS, email, and Messenger/WhatsApp.
- Add consent and master opt-in checks during generation and dispatch.
- Support preferred and fallback channels according to customer policy.
- Implement quiet hours and customer timezones.
- Add retry/backoff for transient failures.
- Record permanent failures, provider IDs, webhook events, and cancellation reasons.

### Exit Criteria

Re-running scheduler or dispatcher jobs creates no duplicate reminders or channel deliveries. Consent, quiet hours, retries, and cancellation behavior are auditable.

## Sprint 7: Vehicle History and Operations Dashboard

### Goals

- Complete the vehicle profile read model.
- Add sections for overview, inspections, photos, paint jobs, PMS history, and notifications.
- Build the customer profile with linked vehicles and contact preferences.
- Add dashboard views for:
  - Today's jobs
  - Active repair work
  - Upcoming PMS
  - Due PMS
  - Overdue PMS
  - Failed notifications
- Add filtering, pagination, loading states, empty states, and error states.
- Add end-to-end tests covering the complete vehicle lifecycle.

### Exit Criteria

Staff can trace a vehicle from intake through inspection, repair or service, schedule, reminder, and notification from one operational experience.

## Sprint 8: Production Hardening and Release

### Goals

- Review API authorization and privacy controls.
- Verify private photo access, upload validation, and credential handling.
- Add webhook authentication and replay protection.
- Test migrations and rollback procedures.
- Configure backups and perform a restore drill.
- Add worker health checks, metrics, structured logs, and alerts.
- Run accessibility, responsive, browser, and performance testing.
- Verify notification providers in sandbox and production modes.
- Conduct user acceptance testing for each staff role.
- Prepare deployment runbooks, release notes, and staff training.

### Exit Criteria

Deployment is repeatable, backups and recovery are tested, worker failures are observable, critical security paths pass, and the product owner approves the MVP scope.

## Parallel Work and Dependencies

- Frontend shell, design tokens, API client, and test harness can begin after Sprint 0.
- Inspection UI and storage integration can proceed once Customer and Vehicle contracts are stable.
- Paint jobs depend on the inspection contract.
- PMS can proceed in parallel with late Paint Job UI after vehicle and odometer foundations are stable.
- Notification adapter contract tests can begin during Sprint 5 while schedule logic is completed.
- Dashboard/read models should wait until source records and identifiers are stable.
- Deployment and observability work can begin incrementally but is finalized in Sprint 8.

## Critical Acceptance Tests

- Changing a plate number does not change vehicle identity or historical foreign keys.
- Lower odometer readings are rejected unless an audited correction includes actor, reason, previous value, and corrected value.
- Editing an inspection after job creation does not modify the job snapshot.
- Failed PMS completion rolls back all related changes.
- Re-running reminder generation and delivery creates no duplicates.
- Opting out cancels unsent notifications while preserving sent history.
- Every role is denied unauthorized API mutations, even if the UI is bypassed.
- Vehicle profiles link back to source records and do not become a second editable source of truth.

## Deferred Features

The following features are outside the MVP:

- Customer portal
- Online booking
- Payments
- Inventory management
- AI recommendations
- Multi-branch administration
- Accounting integrations
- Non-MVP documents and digital signatures

## Current Implementation Status

The implemented project foundation and Sprint 3 increment include:

- FastAPI backend with health and shop configuration endpoints
- Angular standalone frontend shell
- Responsive operations dashboard foundation
- Development proxy between Angular and FastAPI
- Backend tests and frontend production build
- Resumable vehicle intake drafts with one active draft per vehicle
- Structured inspection concerns with area, condition, severity, requested work,
  technician notes, and recommendations
- Private server-generated photo keys with MIME, size, and image-dimension validation
- Five-minute signed photo URLs and role-enforced photo access metadata
- Dashboard intake, inspection, upload-progress, retry, and failure states

Sprint 5 is implemented in the backend with:

- Draft, completed, and cancelled PMS service records with items, parts, labor,
  calculated costs, recommendations, and operational immutability
- Transactional PMS completion that accepts the odometer and creates schedules
  atomically, with rollback on validation failure
- Date-only, odometer-only, whichever-comes-first, and whichever-comes-last
  schedule rules with deterministic evaluation
- Active schedule supersession and append-only schedule state history
