import json

import pytest
import tcm_ai.api.wx_user_auth as wx_user_auth_module
import tcm_ai.core.config_store as config_store_module
import tcm_ai.services.user_service as user_service_module
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tcm_ai.api.app import create_app
from tcm_ai.api.routes.vitals import router as vitals_router
from tcm_ai.domain.pulse.synthetic import synthetic_pulse_waveform
from tcm_ai.domain.vitals.constants import VITALS_MAX_SAMPLES
from tcm_ai.services.user_service import WxUserService
from tcm_ai.services.wx_token import issue_token


@pytest.fixture
def client():
    with TestClient(create_app()) as test_client:
        yield test_client


def test_vitals_analyze_api(client):
    samples = synthetic_pulse_waveform(duration_sec=10.0, fs=100.0, bpm=70.0)
    resp = client.post(
        "/api/vitals/analyze",
        json={"samples": samples, "fs": 100.0, "source": "test"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["heart_rate"] > 0
    assert body["overall_status"]


def test_vitals_analyze_rejects_short_samples(client):
    resp = client.post(
        "/api/vitals/analyze",
        json={"samples": [1.0, 2.0, 3.0], "fs": 100.0, "source": "test"},
    )
    assert resp.status_code == 422


def test_vitals_analyze_rejects_oversized_payload(client):
    resp = client.post(
        "/api/vitals/analyze",
        json={
            "samples": [1.0] * (VITALS_MAX_SAMPLES + 1),
            "fs": 100.0,
            "source": "test",
        },
    )
    assert resp.status_code == 422


def test_vitals_production_requires_auth_or_public_flag(tmp_path, monkeypatch):
    users_file = tmp_path / "wx_users.json"
    cfg_path = tmp_path / "admin_config.json"
    cfg_path.write_text(
        json.dumps(
            {
                "admin_api_key": "test-admin-key-thirty-two-chars-min",
                "server": {
                    "cors_origins": ["https://example.com"],
                    "allow_public_vitals": False,
                },
                "wechat_miniprogram": {
                    "dev_mode": True,
                    "token_secret": "wx-prod-token-" + "a" * 18,
                    "token_ttl_hours": 24,
                },
                "embedding": {"provider": "local", "model": "m", "base_url": "", "api_key": ""},
                "llm": {"provider": "ollama", "model": "m", "base_url": "http://127.0.0.1:11434", "api_key": ""},
                "rerank": {"provider": "none", "model": "", "base_url": "", "api_key": ""},
                "rag": {"rebuild_on_missing_index": False},
                "rbac": {"enabled": False, "keys": []},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("TCM_ENV", "production")
    monkeypatch.setattr(config_store_module, "ADMIN_CONFIG_PATH", str(cfg_path))
    monkeypatch.setattr(config_store_module, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(user_service_module, "USERS_PATH", str(users_file))
    user_service = WxUserService()
    monkeypatch.setattr(wx_user_auth_module, "_user_service", user_service)

    app = FastAPI()
    app.include_router(vitals_router)
    samples = synthetic_pulse_waveform(duration_sec=10.0, fs=100.0, bpm=70.0)
    payload = {"samples": samples, "fs": 100.0, "source": "test"}

    with TestClient(app) as api_client:
        anon = api_client.post("/api/vitals/analyze", json=payload)
        assert anon.status_code == 403

        user = user_service.upsert_by_openid("prod_vitals_test")
        token = issue_token(user["id"])["token"]
        authed = api_client.post(
            "/api/vitals/analyze",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert authed.status_code == 200
        assert authed.json()["success"] is True


def test_vitals_production_rejects_token_for_deleted_user(tmp_path, monkeypatch):
    users_file = tmp_path / "wx_users.json"
    cfg_path = tmp_path / "admin_config.json"
    cfg_path.write_text(
        json.dumps(
            {
                "admin_api_key": "test-admin-key-thirty-two-chars-min",
                "server": {"cors_origins": ["https://example.com"], "allow_public_vitals": False},
                "wechat_miniprogram": {
                    "dev_mode": True,
                    "token_secret": "wx-prod-token-" + "a" * 18,
                    "token_ttl_hours": 24,
                },
                "embedding": {"provider": "local", "model": "m", "base_url": "", "api_key": ""},
                "llm": {"provider": "ollama", "model": "m", "base_url": "http://127.0.0.1:11434", "api_key": ""},
                "rerank": {"provider": "none", "model": "", "base_url": "", "api_key": ""},
                "rag": {"rebuild_on_missing_index": False},
                "rbac": {"enabled": False, "keys": []},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("TCM_ENV", "production")
    monkeypatch.setattr(config_store_module, "ADMIN_CONFIG_PATH", str(cfg_path))
    monkeypatch.setattr(config_store_module, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(user_service_module, "USERS_PATH", str(users_file))
    user_service = WxUserService()
    monkeypatch.setattr(wx_user_auth_module, "_user_service", user_service)

    user = user_service.upsert_by_openid("deleted_user")
    token = issue_token(user["id"])["token"]
    users_file.write_text("{}", encoding="utf-8")

    app = FastAPI()
    app.include_router(vitals_router)
    samples = synthetic_pulse_waveform(duration_sec=10.0, fs=100.0, bpm=70.0)

    with TestClient(app) as api_client:
        resp = api_client.post(
            "/api/vitals/analyze",
            json={"samples": samples, "fs": 100.0, "source": "test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403


def test_analyze_manual_prefers_heart_rate():
    from tcm_ai.services.vitals_service import VitalsService

    service = VitalsService()
    result = service.analyze_manual(heart_rate=80, pulse=55, spo2=98.0)
    assert result.heart_rate == 80
    assert result.hr_status == "正常"
