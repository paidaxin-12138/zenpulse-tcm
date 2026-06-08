import tcm_ai.api.admin_auth as admin_auth_module
import tcm_ai.api.routes.admin as admin_routes_module
import tcm_ai.core.config_store as config_store_module
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tcm_ai.api.routes.admin import router as admin_router


def test_admin_config_update_rejects_insecure_production(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    base_cfg = {
        "admin_api_key": "admin-secret",
        "server": {
            "cors_origins": ["https://example.com"],
            "allow_public_diagnose": False,
            "allow_public_knowledge_search": False,
        },
        "wechat_miniprogram": {"dev_mode": False, "token_secret": "wx-secret"},
        "embedding": {"provider": "local", "model": "m", "base_url": "", "api_key": ""},
        "llm": {"provider": "ollama", "model": "m", "base_url": "http://127.0.0.1:11434", "api_key": ""},
        "rerank": {"provider": "none", "model": "", "base_url": "", "api_key": ""},
        "rag": {},
        "rbac": {"enabled": False, "keys": []},
    }
    monkeypatch.setattr(config_store_module, "load_config", lambda: base_cfg)
    monkeypatch.setattr(admin_auth_module, "load_config", lambda: base_cfg)
    monkeypatch.setattr(admin_routes_module, "load_config", lambda: base_cfg)
    saved = {}

    def _save(cfg):
        saved["cfg"] = cfg

    monkeypatch.setattr(config_store_module, "save_config", _save)

    app = FastAPI()
    app.include_router(admin_router)
    client = TestClient(app)
    headers = {"X-Admin-API-Key": "admin-secret"}

    res = client.put(
        "/api/admin/config",
        headers=headers,
        json={"server": {"allow_public_diagnose": True}},
    )
    assert res.status_code == 400
    assert "allow_public_diagnose" in res.json()["detail"]
    assert "cfg" not in saved
