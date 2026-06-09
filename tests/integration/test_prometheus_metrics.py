# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tcm_ai.api.routes.prometheus_metrics import router as prometheus_router


def test_prometheus_metrics_open_by_default():
    app = FastAPI()
    app.include_router(prometheus_router)
    client = TestClient(app)

    res = client.get("/metrics")
    assert res.status_code == 200
    assert "text/plain" in res.headers.get("content-type", "")
    body = res.text
    assert "tcm_uptime_seconds" in body
    assert "tcm_index_ready" in body
    assert "# TYPE tcm_uptime_seconds gauge" in body


def test_prometheus_metrics_token_gate(monkeypatch):
    monkeypatch.setenv("TCM_METRICS_TOKEN", "secret-metrics")
    app = FastAPI()
    app.include_router(prometheus_router)
    client = TestClient(app)

    assert client.get("/metrics").status_code == 401
    ok = client.get("/metrics", headers={"Authorization": "Bearer secret-metrics"})
    assert ok.status_code == 200
