# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tcm_ai.api.routes.health import router as health_router


def test_health_metrics():
    app = FastAPI()
    app.include_router(health_router)
    client = TestClient(app)
    resp = client.get("/api/health-metrics")
    assert resp.status_code == 200
    body = resp.json()
    assert 30 <= body["heart_rate"] <= 220
    assert "systolic" in body
    assert "diastolic" in body


def test_api_health():
    app = FastAPI()
    app.include_router(health_router)
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_api_ready():
    app = FastAPI()
    app.include_router(health_router)
    client = TestClient(app)
    resp = client.get("/api/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body.get("ready"), bool)
    assert isinstance(body.get("index_ready"), bool)
