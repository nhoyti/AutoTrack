import pytest
from app import main
from app.main import NOTIFICATIONS, REMINDERS, app
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_in_memory_state():
    for store in (
        main.CUSTOMERS,
        main.VEHICLES,
        main.SERVICES,
        main.MAINTENANCE_SCHEDULES,
        main.REMINDERS,
        main.NOTIFICATIONS,
    ):
        store.clear()
    main.NOTIFICATION_ATTEMPTS.clear()
    main.WEBHOOK_EVENTS.clear()
    yield
    for store in (
        main.CUSTOMERS,
        main.VEHICLES,
        main.SERVICES,
        main.MAINTENANCE_SCHEDULES,
        main.REMINDERS,
        main.NOTIFICATIONS,
    ):
        store.clear()
    main.NOTIFICATION_ATTEMPTS.clear()
    main.WEBHOOK_EVENTS.clear()


def login(email: str = "advisor@autotrack.local") -> str:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "autotrack-demo"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def create_due_schedule(token: str, **customer_fields: object) -> tuple[str, str]:
    customer = client.post(
        "/api/customers",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Reminder Customer",
            "mobile_number": "+1-555-0199",
            "email": "reminder@example.com",
            "preferred_contact_method": "SMS",
            **customer_fields,
        },
    ).json()
    vehicle = client.post(
        "/api/vehicles",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "customer_id": customer["customer_id"],
            "plate_number": f"REM-{customer['customer_id'][:6]}",
            "current_odometer": 10000,
        },
    ).json()
    service = client.post(
        "/api/services",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "vehicle_id": vehicle["vehicle_id"],
            "service_date": "2026-09-08",
            "service_type": "PMS",
            "odometer_reading": 10000,
            "items": [
                {
                    "service_category": "PMS",
                    "description": "Oil service",
                    "next_due_date": "2026-09-08",
                    "rule_type": "DATE_ONLY",
                }
            ],
        },
    ).json()
    completed = client.post(
        f"/api/services/{service['service_id']}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert completed.status_code == 200
    return customer["customer_id"], completed.json()["schedule_ids"][0]


def test_reminder_generation_and_dispatch_are_idempotent() -> None:
    token = login()
    customer_id, _ = create_due_schedule(token)
    first = client.post(
        "/api/reminders/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"evaluated_at": "2026-09-08T12:00:00Z"},
    )
    assert first.status_code == 200
    assert first.json()["created_count"] == 1
    notification_count = len(
        [item for item in NOTIFICATIONS.values() if item["customer_id"] == customer_id]
    )

    repeated = client.post(
        "/api/reminders/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"evaluated_at": "2026-09-08T12:00:00Z"},
    )
    assert repeated.json()["created_count"] == 0
    assert (
        len(
            [
                item
                for item in NOTIFICATIONS.values()
                if item["customer_id"] == customer_id
            ]
        )
        == notification_count
    )

    dispatched = client.post(
        "/api/notifications/dispatch",
        headers={"Authorization": f"Bearer {token}"},
        json={"evaluated_at": "2026-09-08T12:00:00Z"},
    )
    assert dispatched.json()["sent"] == notification_count
    assert all(
        item["status"] == "SENT"
        for item in NOTIFICATIONS.values()
        if item["customer_id"] == customer_id
    )


def test_opt_out_cancels_unsent_notifications_and_quiet_hours_defers_dispatch() -> None:
    token = login()
    customer_id, _ = create_due_schedule(
        token,
        quiet_hours_start="09:00",
        quiet_hours_end="17:00",
        email_opt_in=False,
        whatsapp_opt_in=False,
    )
    generated = client.post(
        "/api/reminders/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={"evaluated_at": "2026-09-08T12:00:00Z"},
    )
    assert generated.status_code == 200
    deferred = client.post(
        "/api/notifications/dispatch",
        headers={"Authorization": f"Bearer {token}"},
        json={"evaluated_at": "2026-09-08T12:00:00Z"},
    )
    assert deferred.json()["deferred"] == 1

    preferences = client.patch(
        f"/api/customers/{customer_id}/notification-preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={"master_opt_in": False},
    )
    assert preferences.status_code == 200
    assert all(
        item["status"] == "CANCELLED"
        for item in NOTIFICATIONS.values()
        if item["customer_id"] == customer_id
    )
    assert any(item["customer_id"] == customer_id for item in REMINDERS.values())
