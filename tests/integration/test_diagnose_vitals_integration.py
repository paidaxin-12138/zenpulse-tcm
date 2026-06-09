# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""诊断服务与 vitals_assessment 端到端集成（无 LLM 依赖）。"""

import json

import tcm_ai.api.wx_user_auth as wx_user_auth_module
import tcm_ai.core.config_store as config_store_module
import tcm_ai.services.user_service as user_service_module
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from tcm_ai.api.deps import get_diagnosis_service, get_vision_service
from tcm_ai.api.routes.diagnose import router as diagnose_router
from tcm_ai.domain.pulse.synthetic import synthetic_pulse_waveform
from tcm_ai.services.diagnosis_service import DiagnosisService
from tcm_ai.services.user_service import WxUserService
from tcm_ai.services.vitals_service import VitalsService
from tcm_ai.services.wx_token import issue_token


class FakeVisionService:
    def decode_image(self, _data):
        return None

    def decode_base64_image(self, _data):
        return None

    def analyze_from_images(self, **kwargs):
        return {}


def test_diagnosis_service_run_includes_vitals_from_max30102_waveform():
    service = DiagnosisService()
    samples = synthetic_pulse_waveform(duration_sec=10.0, fs=100.0, bpm=72.0)
    stm_data = {
        "heart_rate": 72,
        "pulse": 72,
        "systolic_pressure": 120,
        "diastolic_pressure": 80,
        "pulse_waveform": samples,
        "pulse_fs": 100.0,
        "pulse_source": "max30102_ble",
    }

    result = service.run({}, stm_data)

    vitals = result["vitals_assessment"]
    assert vitals
    assert vitals.get("heart_rate")
    assert vitals.get("hr_status")
    assert result["pulse_characteristics"] == {}
    assert "生理参数" in result["diagnosis"] or "心率" in result["diagnosis"]


def test_diagnose_json_returns_vitals_assessment_with_real_service():
    app = FastAPI()
    app.include_router(diagnose_router)
    app.dependency_overrides[get_diagnosis_service] = lambda: DiagnosisService()
    app.dependency_overrides[get_vision_service] = lambda: FakeVisionService()

    samples = synthetic_pulse_waveform(duration_sec=10.0, fs=100.0, bpm=68.0)
    payload = {
        "heart_rate": 68,
        "pulse": 68,
        "systolic": 118,
        "diastolic": 76,
        "age": 28,
        "gender": "女",
        "pulse_waveform": samples,
        "pulse_fs": 100.0,
        "pulse_source": "max30102_ble",
    }

    with TestClient(app) as client:
        resp = client.post("/api/diagnose/json", json=payload)

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["vitals_assessment"]
    assert body["vitals_assessment"].get("heart_rate")
    assert body["pulse_characteristics"] == {}


def test_resolve_vitals_passes_through_precomputed_assessment():
    service = DiagnosisService()
    precomputed = {
        "success": True,
        "heart_rate": 71.0,
        "pulse": 71,
        "spo2": 97.5,
        "hr_status": "正常",
        "spo2_status": "正常",
        "overall_status": "正常",
        "source": "max30102_ble",
    }
    samples = synthetic_pulse_waveform(duration_sec=10.0, fs=100.0, bpm=99.0)

    result = service.resolve_vitals_assessment(
        {
            "vitals_assessment": precomputed,
            "pulse_waveform": samples,
            "pulse_source": "max30102_ble",
        }
    )

    assert result["heart_rate"] == 71.0
    assert result["spo2"] == 97.5
    assert result["source"] == "max30102_ble"


def test_resolve_vitals_uses_ch2_for_dual_channel_analysis():
    service = DiagnosisService()
    vitals = VitalsService()
    samples = synthetic_pulse_waveform(duration_sec=10.0, fs=100.0, bpm=72.0)
    ch2 = [int(x * 1.2 + 800) for x in samples]
    expected = vitals.analyze_samples(
        samples, fs=100.0, samples_ch2=ch2, source="max30102_ble"
    ).to_dict()
    ch1_only = vitals.analyze_samples(
        samples, fs=100.0, samples_ch2=None, source="max30102_ble"
    ).to_dict()

    with_ch2 = service.resolve_vitals_assessment(
        {
            "pulse_waveform": samples,
            "max30102_samples_ch2": ch2,
            "pulse_fs": 100.0,
            "pulse_source": "max30102_ble",
        }
    )
    without_ch2 = service.resolve_vitals_assessment(
        {
            "pulse_waveform": samples,
            "pulse_fs": 100.0,
            "pulse_source": "max30102_ble",
        }
    )

    assert with_ch2["spo2"] == expected["spo2"]
    assert without_ch2["spo2"] == ch1_only["spo2"]
    assert with_ch2["spo2"] == expected["spo2"]


def test_diagnose_json_passes_through_vitals_assessment():
    app = FastAPI()
    app.include_router(diagnose_router)
    app.dependency_overrides[get_diagnosis_service] = lambda: DiagnosisService()
    app.dependency_overrides[get_vision_service] = lambda: FakeVisionService()

    precomputed = {
        "success": True,
        "heart_rate": 73.0,
        "pulse": 73,
        "spo2": 96.8,
        "hr_status": "正常",
        "spo2_status": "正常",
        "overall_status": "正常",
        "source": "max30102_ble",
    }
    payload = {
        "heart_rate": 99,
        "pulse": 99,
        "systolic": 120,
        "diastolic": 80,
        "vitals_assessment": precomputed,
        "pulse_waveform": [1.0, 2.0, 3.0],
        "pulse_source": "max30102_ble",
    }

    with TestClient(app) as client:
        resp = client.post("/api/diagnose/json", json=payload)

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["vitals_assessment"]["heart_rate"] == 73.0
    assert resp.json()["vitals_assessment"]["spo2"] == 96.8


def test_diagnose_json_reraises_http_exception():
    class RaisingService:
        def run(self, _vision, _stm):
            raise HTTPException(status_code=403, detail="blocked")

    app = FastAPI()
    app.include_router(diagnose_router)
    app.dependency_overrides[get_diagnosis_service] = lambda: RaisingService()
    app.dependency_overrides[get_vision_service] = lambda: FakeVisionService()

    payload = {
        "heart_rate": 75,
        "pulse": 75,
        "systolic": 120,
        "diastolic": 80,
    }

    with TestClient(app) as client:
        resp = client.post("/api/diagnose/json", json=payload)

    app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert resp.json()["detail"] == "blocked"


def test_resolve_vitals_ignores_failed_precomputed_assessment():
    service = DiagnosisService()
    samples = synthetic_pulse_waveform(duration_sec=10.0, fs=100.0, bpm=72.0)
    stale = {"success": False, "heart_rate": 0.0, "error": "stale payload"}

    result = service.resolve_vitals_assessment(
        {
            "vitals_assessment": stale,
            "pulse_waveform": samples,
            "pulse_fs": 100.0,
            "pulse_source": "max30102_ble",
        }
    )

    assert result["success"] is True
    assert result["heart_rate"] > 0


def test_resolve_vitals_no_manual_fallback_on_ble_analysis_error(monkeypatch):
    service = DiagnosisService()
    samples = synthetic_pulse_waveform(duration_sec=10.0, fs=100.0, bpm=72.0)

    def _boom(*_args, **_kwargs):
        raise RuntimeError("extractor failed")

    monkeypatch.setattr(service._vitals_service, "analyze_samples", _boom)

    result = service.resolve_vitals_assessment(
        {
            "heart_rate": 75,
            "pulse": 75,
            "pulse_waveform": samples,
            "pulse_fs": 100.0,
            "pulse_source": "max30102_ble",
        }
    )

    assert result["success"] is False
    assert "extractor failed" in (result.get("error") or "")


def _production_admin_config(*, allow_public_diagnose: bool) -> dict:
    return {
        "admin_api_key": "test-admin-key-thirty-two-chars-min",
        "server": {
            "cors_origins": ["https://example.com"],
            "allow_public_diagnose": allow_public_diagnose,
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


def test_diagnose_production_requires_auth_or_public_flag(tmp_path, monkeypatch):
    users_file = tmp_path / "wx_users.json"
    cfg_path = tmp_path / "admin_config.json"
    cfg_path.write_text(
        json.dumps(_production_admin_config(allow_public_diagnose=False)),
        encoding="utf-8",
    )

    monkeypatch.setenv("TCM_ENV", "production")
    monkeypatch.setattr(config_store_module, "ADMIN_CONFIG_PATH", str(cfg_path))
    monkeypatch.setattr(config_store_module, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(user_service_module, "USERS_PATH", str(users_file))
    user_service = WxUserService()
    monkeypatch.setattr(wx_user_auth_module, "_user_service", user_service)

    app = FastAPI()
    app.include_router(diagnose_router)
    app.dependency_overrides[get_diagnosis_service] = lambda: DiagnosisService()
    app.dependency_overrides[get_vision_service] = lambda: FakeVisionService()

    payload = {
        "heart_rate": 75,
        "pulse": 75,
        "systolic": 120,
        "diastolic": 80,
    }

    with TestClient(app) as client:
        anon = client.post("/api/diagnose/json", json=payload)
        assert anon.status_code == 403

        user = user_service.upsert_by_openid("prod_diagnose_test")
        token = issue_token(user["id"])["token"]
        authed = client.post(
            "/api/diagnose/json",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert authed.status_code == 200
        assert authed.json()["vitals_assessment"]

    app.dependency_overrides.clear()
