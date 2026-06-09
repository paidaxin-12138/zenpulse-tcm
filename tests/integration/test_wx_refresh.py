# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import tcm_ai.api.routes.wx_auth as wx_auth_module
import tcm_ai.services.user_service as user_service_module
import tcm_ai.services.wechat_auth_service as wechat_auth_module
import tcm_ai.services.wx_token as wx_token_module
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tcm_ai.api.routes.wx_auth import router as wx_auth_router
from tcm_ai.services.user_service import WxUserService

_WX_CFG = {
    "dev_mode": True,
    "token_ttl_hours": 24,
    "token_refresh_grace_hours": 168,
}


def test_wx_refresh_returns_new_token(tmp_path, monkeypatch):
    users_file = tmp_path / "wx_users.json"
    monkeypatch.setattr(user_service_module, "USERS_PATH", str(users_file))
    monkeypatch.setattr(wx_auth_module, "_user_service", WxUserService())
    cfg = {"wechat_miniprogram": _WX_CFG}
    monkeypatch.setattr(wx_token_module, "load_config", lambda: cfg)
    monkeypatch.setattr(wechat_auth_module, "load_config", lambda: cfg)

    app = FastAPI()
    app.include_router(wx_auth_router)
    client = TestClient(app)

    login = client.post("/api/wx/login", json={"code": "refresh-user"})
    assert login.status_code == 200
    body = login.json()
    assert body.get("expires_in") == 24 * 3600
    old_token = body["token"]

    refreshed = client.post(
        "/api/wx/refresh",
        headers={"Authorization": f"Bearer {old_token}"},
    )
    assert refreshed.status_code == 200
    data = refreshed.json()
    assert data["token"]
    assert data["expires_in"] == 24 * 3600
    assert data["user"]["id"] == body["user"]["id"]

    me = client.get("/api/wx/me", headers={"Authorization": f"Bearer {data['token']}"})
    assert me.status_code == 200
