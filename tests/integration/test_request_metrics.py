# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tcm_ai.api.middleware.request_metrics import RequestMetricsMiddleware
from tcm_ai.api.routes.prometheus_metrics import router as prometheus_router
from tcm_ai.core.request_metrics import reset_counters_for_tests


def test_http_request_counter_middleware():
    reset_counters_for_tests()
    app = FastAPI()
    app.add_middleware(RequestMetricsMiddleware)

    @app.get("/api/health")
    def health():
        return {"ok": True}

    app.include_router(prometheus_router)
    client = TestClient(app)

    assert client.get("/api/health").status_code == 200
    assert client.get("/api/health").status_code == 200

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    body = metrics.text
    assert "tcm_http_requests_total" in body
    assert 'route="/api/health"' in body
    assert 'method="GET"' in body
