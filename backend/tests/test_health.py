from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_returns_service_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "autotrack-api"


def test_shop_config_returns_operational_defaults() -> None:
    response = client.get("/api/config/shop")

    assert response.status_code == 200
    assert response.json() == {
        "timezone": "UTC",
        "currency": "USD",
        "odometer_unit": "km",
    }


def test_api_meta_exposes_foundation_conventions() -> None:
    response = client.get("/api/meta")

    assert response.status_code == 200
    assert response.json() == {
        "api_version": "0.1.0",
        "environment": "development",
        "timestamp_policy": "UTC ISO 8601",
    }
