# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from fastapi.testclient import TestClient

from tcm_ai.api.app import app


def test_public_system_status():
    client = TestClient(app)
    resp = client.get("/api/system/status")
    assert resp.status_code == 200
    body = resp.json()
    assert "rag_deps_ok" in body
    assert "ollama_ok" in body
    assert "index_ready" in body


def test_legal_pages():
    client = TestClient(app)
    for page in ("privacy", "terms", "algorithm"):
        resp = client.get(f"/legal/{page}")
        assert resp.status_code == 200
