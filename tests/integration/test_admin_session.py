# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import tcm_ai.api.admin_auth as admin_auth_module
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tcm_ai.api.routes.admin import router as admin_router
from tcm_ai.api.routes.admin_session import router as admin_session_router


def _app(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "development")
    monkeypatch.setattr(
        admin_auth_module,
        "load_config",
        lambda: {"admin_api_key": "session-key", "rbac": {"enabled": False}},
    )
    app = FastAPI()
    app.include_router(admin_session_router)
    app.include_router(admin_router)
    return TestClient(app)


def test_admin_session_login_cookie_auth_logout(monkeypatch):
    client = _app(monkeypatch)

    bad = client.post("/api/admin/session/login", json={"api_key": "wrong"})
    assert bad.status_code == 401

    login = client.post("/api/admin/session/login", json={"api_key": "session-key", "display_name": "Ops"})
    assert login.status_code == 200
    assert login.json()["role"] == "admin"
    assert "tcm_admin_session" in login.cookies
    saved_cookie = login.cookies.get("tcm_admin_session")

    me = client.get("/api/admin/me")
    assert me.status_code == 200
    assert me.json()["role"] == "admin"

    cfg = client.get("/api/admin/config")
    assert cfg.status_code == 200

    logout = client.post("/api/admin/session/logout")
    assert logout.status_code == 200

    after = client.get("/api/admin/config")
    assert after.status_code == 401

    if saved_cookie:
        client.cookies.set("tcm_admin_session", saved_cookie)
        assert client.get("/api/admin/me").status_code == 401


def test_admin_header_still_works_without_cookie(monkeypatch):
    client = _app(monkeypatch)
    res = client.get("/api/admin/me", headers={"X-Admin-API-Key": "session-key"})
    assert res.status_code == 200
