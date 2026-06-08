import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tcm_ai.api.deps import get_diagnosis_service, get_vision_service
from tcm_ai.api.routes.diagnose import router as diagnose_router
from tcm_ai.domain.constants import DEFAULT_PULSE_CHARACTERISTICS, DISCLAIMER
from tcm_ai.domain.rules import RuleEngine


class FakeDiagnosisService:
    def run(self, vision_data, stm_data):
        return {
            "diagnosis": "1. 中医辨证：气血不足\n3. 证候分析：测试分析内容",
            "source": "测试来源",
            "pulse_characteristics": DEFAULT_PULSE_CHARACTERISTICS,
            "disclaimer": DISCLAIMER,
            "syndrome": "气血不足",
            "analysis": "测试分析内容",
            "suggestions": ["均衡饮食", "保证睡眠"],
            "prescriptions": ["八珍汤加减"],
            "face_analysis": ["面色苍白"],
            "tongue_analysis": [],
            "eye_analysis": [],
            "fusion_summary": None,
        }


class FakeVisionService:
    def decode_image(self, _data):
        return None

    def decode_base64_image(self, _data):
        return None

    def analyze_from_images(self, **kwargs):
        return {"face": {"skin_color": {"hue": 10, "saturation": 0.3, "value": 0.8}}}


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(diagnose_router)
    app.dependency_overrides[get_diagnosis_service] = lambda: FakeDiagnosisService()
    app.dependency_overrides[get_vision_service] = lambda: FakeVisionService()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_diagnose_json_structured_response(client):
    payload = {
        "heart_rate": 75,
        "pulse": 75,
        "systolic": 120,
        "diastolic": 80,
        "age": 30,
        "gender": "男",
    }
    resp = client.post("/api/diagnose/json", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["syndrome"] == "气血不足"
    assert body["analysis"] == "测试分析内容"
    assert len(body["suggestions"]) == 2
    assert body["disclaimer"] == DISCLAIMER


def test_diagnose_multipart_without_optional_age(client):
    resp = client.post(
        "/api/diagnose",
        data={
            "heart_rate": "72",
            "pulse": "72",
            "systolic": "120",
            "diastolic": "80",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["syndrome"] == "气血不足"


def test_rule_engine_returns_structured():
    vision_data = {
        "face": {"skin_color": {"hue": 10, "saturation": 0.3, "value": 0.8}},
        "tongue": {"color": {"hsv": [15, 0.2, 0.7]}, "coating": {"coating_ratio": 0.2}},
        "eyes": [{"bloodshot": {"red_ratio": 0.1, "severity": "轻度"}}],
    }
    stm_data = {"heart_rate": 75, "systolic_pressure": 110, "diastolic_pressure": 70}
    result = RuleEngine.diagnose(vision_data, stm_data)
    assert "structured" in result
    assert result["structured"]["syndrome"]
    assert isinstance(result["structured"]["suggestions"], list)
