# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import tcm_ai.api.routes.history as history_module
import tcm_ai.api.routes.wx_auth as wx_auth_module
import tcm_ai.core.config_store as config_store_module
import tcm_ai.services.history_service as history_service_module
import tcm_ai.services.user_service as user_service_module
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tcm_ai.api.routes.history import router as history_router
from tcm_ai.api.routes.wx_auth import router as wx_auth_router
from tcm_ai.services.history_service import DiagnosisHistoryService
from tcm_ai.services.user_service import WxUserService


def test_wx_login_dev_mode(tmp_path, monkeypatch):
    users_file = tmp_path / "wx_users.json"
    monkeypatch.setattr(user_service_module, "USERS_PATH", str(users_file))
    monkeypatch.setattr(
        wx_auth_module,
        "_user_service",
        WxUserService(),
    )
    monkeypatch.setattr(
        config_store_module,
        "load_config",
        lambda: {
            "admin_api_key": "test-admin-key",
            "wechat_miniprogram": {"dev_mode": True, "token_ttl_hours": 24},
        },
    )

    app = FastAPI()
    app.include_router(wx_auth_router)
    client = TestClient(app)

    res = client.post("/api/wx/login", json={"code": "simulator-code-001"})
    assert res.status_code == 200
    body = res.json()
    assert body["token"]
    assert body["user"]["nickName"].startswith("微信用户")

    me = client.get("/api/wx/me", headers={"Authorization": f"Bearer {body['token']}"})
    assert me.status_code == 200
    assert me.json()["user"]["id"] == body["user"]["id"]


def test_diagnosis_history_scoped_by_wx_user(tmp_path, monkeypatch):
    history_dir = tmp_path / "history"
    history_file = tmp_path / "diagnosis_history.json"
    detail_dir = tmp_path / "history_details"
    users_file = tmp_path / "wx_users.json"

    monkeypatch.setattr(history_service_module, "HISTORY_PATH", str(history_file))
    monkeypatch.setattr(history_service_module, "HISTORY_USER_DIR", str(history_dir))
    monkeypatch.setattr(history_service_module, "HISTORY_DETAIL_DIR", str(detail_dir))
    monkeypatch.setattr(user_service_module, "USERS_PATH", str(users_file))
    user_service = WxUserService()
    monkeypatch.setattr(wx_auth_module, "_user_service", user_service)
    import tcm_ai.api.wx_user_auth as wx_user_auth_module

    monkeypatch.setattr(wx_user_auth_module, "_user_service", user_service)
    monkeypatch.setattr(
        config_store_module,
        "load_config",
        lambda: {
            "admin_api_key": "test-admin-key",
            "wechat_miniprogram": {"dev_mode": True},
        },
    )

    history_svc = DiagnosisHistoryService()
    monkeypatch.setattr(history_module, "_service", history_svc)

    app = FastAPI()
    app.include_router(wx_auth_router)
    app.include_router(history_router)
    client = TestClient(app)

    login = client.post("/api/wx/login", json={"code": "user-a"})
    token_a = login.json()["token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    login_b = client.post("/api/wx/login", json={"code": "user-b"})
    token_b = login_b.json()["token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    assert client.get("/api/diagnosis/history").status_code == 401
    assert client.get("/api/diagnosis/history", headers=headers_a).json()["total"] == 0

    client.post(
        "/api/diagnosis/history",
        headers=headers_a,
        json={"syndrome": "气虚", "diagnosis": "用户A报告"},
    )
    client.post(
        "/api/diagnosis/history",
        headers=headers_b,
        json={"syndrome": "血虚", "diagnosis": "用户B报告"},
    )

    assert client.get("/api/diagnosis/history", headers=headers_a).json()["total"] == 1
    assert client.get("/api/diagnosis/history", headers=headers_b).json()["total"] == 1
    assert client.get("/api/diagnosis/history").status_code == 401
