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
