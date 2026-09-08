from fastapi.testclient import TestClient

from app.main import app, MAINTENANCE_SCHEDULES

client = TestClient(app)


def login(email: str = "advisor@autotrack.local") -> str:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "autotrack-demo"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def create_vehicle(token: str, odometer: int = 10000) -> str:
    customer = client.post(
        "/api/customers",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "PMS Test Customer"},
    ).json()
    vehicle = client.post(
        "/api/vehicles",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer["customer_id"],
            "plate_number": f"PMS-{customer['customer_id'][:6]}",
            "current_odometer": odometer,
        },
    ).json()
    return vehicle["vehicle_id"]


def create_service(token: str, vehicle_id: str, **item: object) -> dict:
    response = client.post(
        "/api/services",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "vehicle_id": vehicle_id,
            "service_date": "2026-09-08",
            "service_type": "PMS",
            "odometer_reading": 11000,
            "labor_cost": 50,
            "parts": [{"part_name": "Oil filter", "quantity": 2, "unit_cost": 8}],
            "items": [{"service_category": "PMS", "description": "Routine service", **item}],
        },
    )
    assert response.status_code == 201
    return response.json()


def test_pms_completion_is_idempotent_and_supersedes_active_schedule() -> None:
    token = login()
    vehicle_id = create_vehicle(token)
    first = create_service(
        token,
        vehicle_id,
        next_due_date="2027-03-08",
        next_due_odometer=20000,
        rule_type="WHICHEVER_COMES_FIRST",
    )
    completed = client.post(
        f"/api/services/{first['service_id']}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert completed.status_code == 200
    schedule_id = completed.json()["schedule_ids"][0]
    assert len(MAINTENANCE_SCHEDULES) == 1

    repeated = client.post(
        f"/api/services/{first['service_id']}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert repeated.status_code == 200
    assert repeated.json()["schedule_ids"] == [schedule_id]
    assert len(MAINTENANCE_SCHEDULES) == 1

    second = create_service(
        token,
        vehicle_id,
        next_due_date="2028-03-08",
        next_due_odometer=30000,
        rule_type="WHICHEVER_COMES_FIRST",
    )
    second_completed = client.post(
        f"/api/service-records/{second['service_id']}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert second_completed.status_code == 200
    schedules = client.get(
        "/api/maintenance-schedules",
        headers={"Authorization": f"Bearer {token}"},
        params={"vehicle_id": vehicle_id},
    ).json()
    assert len(schedules) == 2
    old = next(schedule for schedule in schedules if schedule["schedule_id"] == schedule_id)
    assert old["status"] == "SKIPPED"
    assert old["superseded_by_schedule_id"] == second_completed.json()["schedule_ids"][0]


def test_failed_completion_rolls_back_odometer_and_schedule_changes() -> None:
    token = login()
    vehicle_id = create_vehicle(token, odometer=20000)
    service = create_service(
        token,
        vehicle_id,
        next_due_odometer=30000,
        rule_type="ODOMETER_ONLY",
    )
    response = client.post(
        f"/api/services/{service['service_id']}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "ODOMETER_REGRESSION"
    vehicle = client.get(
        f"/api/vehicles/{vehicle_id}",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert vehicle["current_odometer"] == 20000
    assert not any(schedule["vehicle_id"] == vehicle_id for schedule in MAINTENANCE_SCHEDULES.values())


def test_completed_service_is_immutable_and_rules_evaluate_deterministically() -> None:
    token = login()
    vehicle_id = create_vehicle(token)
    service = create_service(
        token,
        vehicle_id,
        next_due_date="2026-09-08",
        next_due_odometer=12000,
        rule_type="WHICHEVER_COMES_LAST",
    )
    completed = client.post(
        f"/api/services/{service['service_id']}/complete",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    schedule_id = completed["schedule_ids"][0]
    evaluated = client.post(
        f"/api/maintenance-schedules/{schedule_id}/evaluate",
        headers={"Authorization": f"Bearer {token}"},
        json={"evaluated_at": "2026-09-08T12:00:00Z", "odometer": 11000},
    )
    assert evaluated.status_code == 200
    assert evaluated.json()["evaluated_status"] == "PLANNED"

    update = client.patch(
        f"/api/services/{service['service_id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={"description": "Attempted correction"},
    )
    assert update.status_code == 409
