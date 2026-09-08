import base64

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def login(email: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "autotrack-demo"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def create_vehicle(token: str) -> str:
    customer = client.post(
        "/api/customers",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Intake Test Customer"},
    ).json()
    vehicle = client.post(
        "/api/vehicles",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer["customer_id"],
            "plate_number": "INTAKE-" + customer["customer_id"][:6],
        },
    ).json()
    return vehicle["vehicle_id"]


def test_intake_resume_and_structured_inspection_completion() -> None:
    token = login("advisor@autotrack.local")
    vehicle_id = create_vehicle(token)
    headers = {"Authorization": f"Bearer {token}"}

    first = client.post(
        "/api/intakes",
        headers=headers,
        json={"vehicle_id": vehicle_id, "notes": "Customer waiting"},
    )
    resumed = client.post(
        "/api/intakes",
        headers=headers,
        json={"vehicle_id": vehicle_id},
    )
    assert first.status_code == 201
    assert resumed.status_code == 201
    assert resumed.json()["intake_id"] == first.json()["intake_id"]

    inspection = client.post(
        "/api/inspections",
        headers=headers,
        json={
            "intake_id": first.json()["intake_id"],
            "concerns": [
                {
                    "area": "Front bumper",
                    "condition": "Deep scrape",
                    "severity": "HIGH",
                    "requested_work": "Prepare and repaint",
                    "technician_notes": "Check mounting clips",
                    "recommendation": "Include in body estimate",
                }
            ],
        },
    )
    assert inspection.status_code == 201
    inspection_id = inspection.json()["inspection_id"]

    completed = client.post(
        f"/api/inspections/{inspection_id}/complete", headers=headers
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "COMPLETED"

    update = client.patch(
        f"/api/inspections/{inspection_id}",
        headers=headers,
        json={"concerns": []},
    )
    assert update.status_code == 409


def test_photo_upload_returns_private_signed_url_and_rejects_mime() -> None:
    token = login("technician@autotrack.local")
    vehicle_id = create_vehicle(login("advisor@autotrack.local"))
    advisor_headers = {"Authorization": f"Bearer {login('advisor@autotrack.local')}"}
    intake = client.post(
        "/api/intakes", headers=advisor_headers, json={"vehicle_id": vehicle_id}
    ).json()
    inspection = client.post(
        "/api/inspections",
        headers={"Authorization": f"Bearer {token}"},
        json={"intake_id": intake["intake_id"], "concerns": []},
    ).json()
    headers = {"Authorization": f"Bearer {token}"}

    unsupported = client.post(
        f"/api/inspections/{inspection['inspection_id']}/photos",
        headers=headers,
        files={"file": ("notes.txt", b"not an image", "text/plain")},
    )
    assert unsupported.status_code == 415

    uploaded = client.post(
        f"/api/inspections/{inspection['inspection_id']}/photos",
        headers=headers,
        files={"file": ("front.png", PNG_1X1, "image/png")},
    )
    assert uploaded.status_code == 201
    photo = uploaded.json()
    assert photo["storage_key"].startswith("inspections/")
    assert "token=" in photo["url"]
    content = client.get(photo["url"])
    assert content.status_code == 200
    assert content.headers["content-type"] == "image/png"


def test_read_only_cannot_mutate_intake() -> None:
    token = login("viewer@autotrack.local")
    response = client.post(
        "/api/intakes",
        headers={"Authorization": f"Bearer {token}"},
        json={"vehicle_id": "missing"},
    )
    assert response.status_code == 403
