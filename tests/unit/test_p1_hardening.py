import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from tcm_ai.api.admin_auth import require_admin_role
from tcm_ai.api.routes.admin import router as admin_router
from tcm_ai.api.routes.health import router as health_router
from tcm_ai.core.url_safety import UnsafeUrlError, validate_outbound_base_url


def test_api_ready_endpoint():
    app = FastAPI()
    app.include_router(health_router)
    client = TestClient(app)
    res = client.get("/api/ready")
    assert res.status_code == 200
    body = res.json()
    assert "ready" in body
    assert "index_ready" in body


def test_validate_outbound_url_blocks_private_in_production(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    with pytest.raises(UnsafeUrlError):
        validate_outbound_base_url("http://192.168.1.1/v1")


def test_validate_outbound_url_allows_localhost_in_development(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "development")
    assert validate_outbound_base_url("http://127.0.0.1:11434") == "http://127.0.0.1:11434"


def test_admin_auth_rate_limit(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "development")
    import tcm_ai.api.admin_auth as admin_auth_module

    cfg = {"admin_api_key": "good-key", "rbac": {"enabled": False}}
    monkeypatch.setattr(admin_auth_module, "load_config", lambda: cfg)

    app = FastAPI()
    app.include_router(admin_router)

    @app.get("/probe")
    def probe(role: str = Depends(require_admin_role("viewer"))):
        return {"ok": True, "role": role}

    client = TestClient(app)
    for _ in range(20):
        assert client.get("/probe", headers={"X-Admin-API-Key": "bad"}).status_code == 401
    res = client.get("/probe", headers={"X-Admin-API-Key": "bad"})
    assert res.status_code == 429

    ok = client.get("/probe", headers={"X-Admin-API-Key": "good-key"})
    assert ok.status_code == 200
    retry = client.get("/probe", headers={"X-Admin-API-Key": "bad"})
    assert retry.status_code == 401
