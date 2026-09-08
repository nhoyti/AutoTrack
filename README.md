# AutoTrack

AutoTrack is an internal staff application for an autohaus/body-repair shop. It follows the operational lifecycle:

`Customer -> Vehicle -> Inspection -> Job -> Service -> Reminder -> Notification -> Dashboard`

## Current foundation

- `backend/`: FastAPI service with health and shop configuration endpoints.
- `frontend/`: Angular standalone application with the first staff operations dashboard shell.
- `AutoTrack_Architecture.md`: domain model, workflows, data rules, and MVP scope.

## Run locally

### Backend

```bash
python3 -m venv .venv
make install
.venv/bin/uvicorn app.main:app --app-dir backend --reload
```

The API is available at `http://localhost:8000`. OpenAPI documentation is at `/docs`.

### Sprint 1 authentication

The local foundation includes staff login at `POST /api/auth/login`, the current
staff identity endpoint at `GET /api/auth/me`, and API-enforced role access for
the staff directory at `GET /api/admin/staff`. The Angular dashboard is guarded
by the same bearer session.

For local development, the seeded staff accounts use the password
`autotrack-demo`. Set `AUTOTRACK_DEMO_PASSWORD` and a strong
`AUTOTRACK_AUTH_SECRET` before using the API outside local development.

### Frontend

```bash
npm install --prefix frontend
npm start --prefix frontend
```

The Angular application is available at `http://localhost:4200`; `proxy.conf.json` forwards `/health` and `/api` to the local backend.

### Sprint 3 intake and inspections

The dashboard supports resumable vehicle intake, structured inspection concerns,
and private image uploads. Photo uploads accept JPEG, PNG, and GIF files up to
10 MB, validate image dimensions, and return five-minute signed content URLs.

### Quality checks

```bash
make check
```

This runs backend tests, Ruff linting and formatting checks, and the Angular production build. Copy `backend/.env.example` to `backend/.env` to override local shop settings; all timestamps exchanged by the API use UTC ISO 8601 values.

## Development direction

The implemented slices cover staff authentication, Customer and Vehicle records,
Intake and Digital Inspections, and PMS service records with maintenance
schedules. Features outside the MVP, including customer portal, booking,
payments, inventory, AI recommendations, and multi-branch administration, remain
deferred.
