from app.database import SessionLocal
from app.models import Alert, MonitoredService
from app.services.monitoring import ProbeResult, record_result

NEW_SERVICE = {"name": "Orders API", "url": "https://orders.example.com/health"}


def test_login_rejects_wrong_password(client):
    response = client.post("/api/auth/login", json={"email": "admin@test.dev", "password": "wrong-password"})
    assert response.status_code == 401


def test_register_then_duplicate_email_conflicts(client):
    body = {"email": "new.user@test.dev", "full_name": "New User", "password": "StrongPass#1"}
    assert client.post("/api/auth/register", json=body).status_code == 201
    assert client.post("/api/auth/register", json=body).status_code == 409


def test_protected_route_requires_token(client):
    assert client.get("/api/services").status_code == 401


def test_viewer_cannot_create_service(client, viewer_headers):
    response = client.post("/api/services", json=NEW_SERVICE, headers=viewer_headers)
    assert response.status_code == 403


def test_admin_can_create_list_update_and_delete(client, admin_headers):
    created = client.post("/api/services", json=NEW_SERVICE, headers=admin_headers)
    assert created.status_code == 201
    service_id = created.json()["id"]

    listing = client.get("/api/services?q=orders", headers=admin_headers).json()
    assert listing["total"] == 1

    patched = client.patch(f"/api/services/{service_id}", json={"is_active": False}, headers=admin_headers)
    assert patched.json()["is_active"] is False

    assert client.delete(f"/api/services/{service_id}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/services/{service_id}", headers=admin_headers).status_code == 404


def test_duplicate_service_name_conflicts(client, admin_headers):
    client.post("/api/services", json=NEW_SERVICE, headers=admin_headers)
    assert client.post("/api/services", json=NEW_SERVICE, headers=admin_headers).status_code == 409


def test_invalid_url_is_rejected(client, admin_headers):
    response = client.post("/api/services", json={"name": "Bad", "url": "not-a-url"}, headers=admin_headers)
    assert response.status_code == 422


def test_three_failures_open_critical_alert_and_recovery_resolves_it(client, admin_headers):
    service_id = client.post("/api/services", json=NEW_SERVICE, headers=admin_headers).json()["id"]
    failure = ProbeResult(False, 503, 5000, "HTTP 503")
    with SessionLocal() as db:
        service = db.get(MonitoredService, service_id)
        for _ in range(3):
            record_result(db, service, failure)
        assert service.status == "down"
        assert db.query(Alert).filter(Alert.severity == "critical", Alert.resolved_at.is_(None)).count() == 1

        record_result(db, service, ProbeResult(True, 200, 90, None))
        assert service.status == "up"
        assert db.query(Alert).filter(Alert.resolved_at.is_(None)).count() == 0

    alerts = client.get("/api/alerts", headers=admin_headers).json()
    assert alerts["total"] >= 1


def test_dashboard_summary_counts_services(client, admin_headers):
    client.post("/api/services", json=NEW_SERVICE, headers=admin_headers)
    summary = client.get("/api/dashboard/summary", headers=admin_headers).json()
    assert summary["total_services"] >= 1
