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


def test_service_advisor_can_create_customer_and_vehicle_record() -> None:
    token = login("advisor@autotrack.local")

    customer_response = client.post(
        "/api/customers",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Nina Patel",
            "mobile_number": "+1-555-0102",
            "email": "nina@example.com",
            "preferred_contact_method": "SMS",
            "status": "ACTIVE",
        },
    )
    assert customer_response.status_code == 201
    customer = customer_response.json()
    assert customer["customer_id"]
    assert customer["full_name"] == "Nina Patel"

    vehicle_response = client.post(
        "/api/vehicles",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer["customer_id"],
            "plate_number": "ABC-123",
            "vin_chassis_number": "1HGBH41JXMN109186",
            "make": "Honda",
            "model": "Civic",
            "year": 2022,
            "color": "Blue",
            "current_odometer": 120000,
        },
    )
    assert vehicle_response.status_code == 201
    vehicle = vehicle_response.json()
    assert vehicle["vehicle_id"]
    assert vehicle["plate_number"] == "ABC-123"
    assert vehicle["current_odometer"] == 120000

    search_response = client.get(
        "/api/vehicles",
        headers={"Authorization": f"Bearer {token}"},
        params={"search": "ABC-123"},
    )
    assert search_response.status_code == 200
    vehicle_matches = search_response.json()
    assert any(item["vehicle_id"] == vehicle["vehicle_id"] for item in vehicle_matches)


def test_odometer_reading_regressions_are_rejected_and_corrections_are_audited() -> (
    None
):
    token = login("advisor@autotrack.local")

    customer_response = client.post(
        "/api/customers",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Oscar Reed",
            "mobile_number": "+1-555-0103",
            "email": "oscar@example.com",
            "preferred_contact_method": "EMAIL",
            "status": "ACTIVE",
        },
    )
    customer = customer_response.json()

    vehicle_response = client.post(
        "/api/vehicles",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer["customer_id"],
            "plate_number": "XYZ-999",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2021,
            "color": "Silver",
            "current_odometer": 98000,
        },
    )
    vehicle = vehicle_response.json()

    regression = client.post(
        f"/api/vehicles/{vehicle['vehicle_id']}/odometer/readings",
        headers={"Authorization": f"Bearer {token}"},
        json={"value": 97000, "source_record": "SERVICE_INTAKE"},
    )
    assert regression.status_code == 400
    assert regression.json()["error"]["code"] == "ODOMETER_REGRESSION"

    correction_response = client.post(
        f"/api/vehicles/{vehicle['vehicle_id']}/odometer/corrections",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "previous_value": 98000,
            "corrected_value": 99000,
            "reason": "Corrected from handheld reading",
            "actor_user_id": "staff-advisor",
        },
    )
    assert correction_response.status_code == 201
    corrected = correction_response.json()
    assert corrected["current_odometer"] == 99000
    assert corrected["readings"][-1]["is_correction"] is True


def test_plate_changes_do_not_change_vehicle_identity() -> None:
    token = login("admin@autotrack.local")

    customer_response = client.post(
        "/api/customers",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Priya Singh",
            "mobile_number": "+1-555-0104",
            "email": "priya@example.com",
            "preferred_contact_method": "SMS",
            "status": "ACTIVE",
        },
    )
    customer = customer_response.json()

    vehicle_response = client.post(
        "/api/vehicles",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer["customer_id"],
            "plate_number": "OLD-555",
            "make": "Ford",
            "model": "Focus",
            "year": 2020,
            "color": "Black",
            "current_odometer": 65000,
        },
    )
    vehicle = vehicle_response.json()

    patched = client.patch(
        f"/api/vehicles/{vehicle['vehicle_id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"plate_number": "NEW-555"},
    )
    assert patched.status_code == 200
    updated = patched.json()
    assert updated["vehicle_id"] == vehicle["vehicle_id"]
    assert updated["plate_number"] == "NEW-555"

    search_response = client.get(
        "/api/vehicles",
        headers={"Authorization": f"Bearer {token}"},
        params={"search": "NEW-555"},
    )
    assert search_response.status_code == 200
    assert any(
        item["vehicle_id"] == vehicle["vehicle_id"] for item in search_response.json()
    )
