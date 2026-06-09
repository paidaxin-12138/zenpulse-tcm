# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tcm_ai.api.routes.system_public import router as system_public_router


def test_public_dev_hints(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "development")
    app = FastAPI()
    app.include_router(system_public_router)
    client = TestClient(app)
    res = client.get("/api/public/dev-hints")
    assert res.status_code == 200
    body = res.json()
    assert "suggested_api_base" in body
    assert "/api" in body["suggested_api_base"]
    assert body.get("checklist")


def test_public_dev_hints_hidden_in_production(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    app = FastAPI()
    app.include_router(system_public_router)
    client = TestClient(app)
    res = client.get("/api/public/dev-hints")
    assert res.status_code == 404
