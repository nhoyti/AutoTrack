from fastapi.testclient import TestClient

from app.main import app


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
