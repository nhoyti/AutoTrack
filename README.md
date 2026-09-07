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

### Frontend

```bash
npm install --prefix frontend
npm start --prefix frontend
```

The Angular application is available at `http://localhost:4200`; `proxy.conf.json` forwards `/health` and `/api` to the local backend.

### Quality checks

```bash
make check
```

This runs backend tests, Ruff linting and formatting checks, and the Angular production build. Copy `backend/.env.example` to `backend/.env` to override local shop settings; all timestamps exchanged by the API use UTC ISO 8601 values.

## Development direction

The next implementation slice is staff authentication and API-enforced roles, followed by Customer and Vehicle records. Features outside the MVP, including customer portal, booking, payments, inventory, AI recommendations, and multi-branch administration, remain deferred.
