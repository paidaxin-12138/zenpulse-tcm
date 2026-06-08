import tcm_ai.api.routes.history as history_module
import tcm_ai.api.routes.wx_auth as wx_auth_module
import tcm_ai.api.wx_user_auth as wx_user_auth_module
import tcm_ai.core.config_store as config_store_module
import tcm_ai.services.history_service as history_service_module
import tcm_ai.services.user_service as user_service_module
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tcm_ai.api.routes.history import router as history_router
from tcm_ai.api.routes.wx_auth import router as wx_auth_router
from tcm_ai.services.history_service import DiagnosisHistoryService
from tcm_ai.services.user_service import WxUserService


def _history_test_app(tmp_path, monkeypatch):
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
    monkeypatch.setattr(wx_user_auth_module, "_user_service", user_service)
    monkeypatch.setattr(
        config_store_module,
        "load_config",
        lambda: {
            "admin_api_key": "test-admin-key",
            "wechat_miniprogram": {"dev_mode": True, "token_ttl_hours": 24},
        },
    )

    history_svc = DiagnosisHistoryService()
    monkeypatch.setattr(history_module, "_service", history_svc)

    app = FastAPI()
    app.include_router(wx_auth_router)
    app.include_router(history_router)
    return TestClient(app)


def test_diagnosis_history_crud(tmp_path, monkeypatch):
    client = _history_test_app(tmp_path, monkeypatch)

    assert client.get("/api/diagnosis/history").status_code == 401

    login = client.post("/api/wx/login", json={"code": "history-user"})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['token']}"}

    assert client.get("/api/diagnosis/history", headers=headers).json()["total"] == 0

    created = client.post(
        "/api/diagnosis/history",
        headers=headers,
        json={
            "syndrome": "气虚",
            "summary": "测试摘要",
            "diagnosis": "完整报告",
            "detail": {
                "syndrome": "气虚",
                "diagnosis": "完整报告",
                "analysis": "深度分析内容",
                "suggestions": ["早睡", "食补"],
            },
        },
    )
    assert created.status_code == 200
    body = created.json()
    entry_id = body["entry"]["id"]
    assert body["entry"]["has_detail"] is True
    assert body["entry"]["detail"]["analysis"] == "深度分析内容"

    listed = client.get("/api/diagnosis/history", headers=headers).json()
    assert listed["total"] == 1
    assert listed["entries"][0]["has_detail"] is True
    assert "detail" not in listed["entries"][0]

    fetched = client.get(f"/api/diagnosis/history/{entry_id}", headers=headers).json()
    assert fetched["entry"]["detail"]["suggestions"] == ["早睡", "食补"]

    assert client.delete(f"/api/diagnosis/history/{entry_id}", headers=headers).status_code == 200
    assert client.delete("/api/diagnosis/history", headers=headers).status_code == 200
