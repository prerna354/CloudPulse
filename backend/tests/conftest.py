import os

os.environ.setdefault("SECRET_KEY", "test-only-secret-key-not-for-production")
os.environ["DATABASE_URL"] = "sqlite:///./test_cloudpulse.db"
os.environ.setdefault("SEED_ADMIN_PASSWORD", "AdminPass#2026")
os.environ.setdefault("SEED_VIEWER_PASSWORD", "ViewerPass#2026")

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import User
from app.security import hash_password


@pytest.fixture(autouse=True)
def fresh_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        db.add_all([
            User(email="admin@test.dev", full_name="Test Admin", role="admin", hashed_password=hash_password("AdminPass#2026")),
            User(email="viewer@test.dev", full_name="Test Viewer", role="viewer", hashed_password=hash_password("ViewerPass#2026")),
        ])
        db.commit()
    yield


@pytest.fixture()
def client():
    return TestClient(app)  # not used as a context manager, so the Redis listener is not started


def _login(client, email, password):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture()
def admin_headers(client):
    return _login(client, "admin@test.dev", "AdminPass#2026")


@pytest.fixture()
def viewer_headers(client):
    return _login(client, "viewer@test.dev", "ViewerPass#2026")
