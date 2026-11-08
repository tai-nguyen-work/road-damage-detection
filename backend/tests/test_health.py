import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@localhost/test")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.schemas.health import HealthResponse  # noqa: E402
from app.services.health import check_health  # noqa: E402


def test_health_ready() -> None:
    app.dependency_overrides[check_health] = lambda: HealthResponse(
        status="ok", database="ok", postgis="ok", schema="ok", redis="ok"
    )
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/health")
            assert response.status_code == 200
            assert response.json()["postgis"] == "ok"
    finally:
        app.dependency_overrides.clear()


def test_health_unavailable_does_not_expose_credentials() -> None:
    app.dependency_overrides[check_health] = lambda: HealthResponse(
        status="degraded", database="error", postgis="error", schema="error", redis="error"
    )
    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/health")
            assert response.status_code == 503
            assert "postgresql" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_health_checks_dependency_failures(monkeypatch) -> None:
    def unavailable():
        raise ConnectionError("sensitive password")

    monkeypatch.setattr("app.services.health.get_engine", unavailable)
    monkeypatch.setattr("app.services.health.Redis.from_url", lambda *a, **kw: unavailable())
    result = check_health()
    assert result.status == "degraded"
    assert result.database == result.redis == "error"


def test_openapi() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()
        assert "/api/v1/health" in schema["paths"]
        assert "503" in schema["paths"]["/api/v1/health"]["get"]["responses"]
