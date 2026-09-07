PYTHON := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: install install-backend install-frontend test lint format-check check dev-api dev-frontend

install: install-backend install-frontend

install-backend:
	$(PIP) install -e 'backend[dev]'

install-frontend:
	npm install --prefix frontend

test:
	$(PYTHON) -m pytest backend/tests -q
	npm run check --prefix frontend

lint:
	$(PYTHON) -m ruff check backend/app backend/tests

format-check:
	$(PYTHON) -m ruff format --check backend/app backend/tests

check: test lint format-check

dev-api:
	$(PYTHON) -m uvicorn app.main:app --app-dir backend --reload

dev-frontend:
	npm start --prefix frontend