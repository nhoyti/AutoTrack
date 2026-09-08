from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def login(email: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "autotrack-demo"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_staff_can_sign_in_and_read_their_identity() -> None:
    token = login("advisor@autotrack.local")

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "SERVICE_ADVISOR"


def test_invalid_credentials_are_rejected_with_api_error() -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "advisor@autotrack.local", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_protected_endpoint_requires_authentication() -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_admin_can_read_staff_directory() -> None:
    token = login("admin@autotrack.local")

    response = client.get(
        "/api/admin/staff",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 4


def test_read_only_staff_cannot_access_admin_endpoint() -> None:
    token = login("viewer@autotrack.local")

    response = client.get(
        "/api/admin/staff",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_read_only_staff_cannot_mutate_audit_events() -> None:
    token = login("viewer@autotrack.local")

    response = client.post(
        "/api/admin/audit/events",
        headers={"Authorization": f"Bearer {token}"},
        json={"event_type": "UNAUTHORIZED_TEST"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_successful_login_is_audited() -> None:
    token = login("technician@autotrack.local")

    response = client.get(
        "/api/audit/events",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()[-1]["event_type"] == "STAFF_LOGIN"
    assert response.json()[-1]["occurred_at"].endswith("Z")
