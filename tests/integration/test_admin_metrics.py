# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import tcm_ai.api.admin_auth as admin_auth_module
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tcm_ai.api.routes.metrics import router as metrics_router


def test_admin_metrics_requires_key(monkeypatch):
    monkeypatch.setattr(
        admin_auth_module,
        "load_config",
        lambda: {"admin_api_key": "metrics-key", "rbac": {"enabled": False}},
    )
    app = FastAPI()
    app.include_router(metrics_router)
    client = TestClient(app)

    assert client.get("/api/admin/metrics").status_code == 401

    res = client.get("/api/admin/metrics", headers={"X-Admin-API-Key": "metrics-key"})
    assert res.status_code == 200
    body = res.json()
    assert "uptime_seconds" in body
    assert "index_ready" in body
    assert body["history_backend"] in ("json", "sql")
