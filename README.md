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
.venv/bin/pip install "fastapi>=0.115,<1.0" "uvicorn[standard]>=0.30,<1.0" "pydantic-settings>=2.6,<3.0" "httpx>=0.27,<1.0" "pytest>=8.3,<9.0"
.venv/bin/uvicorn app.main:app --app-dir backend --reload
```

The API is available at `http://localhost:8000`. OpenAPI documentation is at `/docs`.

### Frontend

```bash
npm install --prefix frontend
npm start --prefix frontend
```

The Angular application is available at `http://localhost:4200`; `proxy.conf.json` forwards `/health` and `/api` to the local backend.

## Development direction

The next implementation slice is staff authentication and API-enforced roles, followed by Customer and Vehicle records. Features outside the MVP, including customer portal, booking, payments, inventory, AI recommendations, and multi-branch administration, remain deferred.
