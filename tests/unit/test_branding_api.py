# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tcm_ai.api.routes.system_public import router as system_public_router


def test_public_branding():
    app = FastAPI()
    app.include_router(system_public_router)
    client = TestClient(app)
    res = client.get("/api/public/branding")
    assert res.status_code == 200
    body = res.json()
    assert body["brandName"]
    assert body["links"]["web"] == "/"
    assert body["links"]["admin"] == "/admin"
    assert body["miniprogram"]["name"]
