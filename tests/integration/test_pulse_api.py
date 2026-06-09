from unittest.mock import MagicMock

import json

import pytest
from fastapi.testclient import TestClient

from tcm_ai.api.app import create_app
from tcm_ai.api.deps import get_diagnosis_service
from tcm_ai.domain.pulse.synthetic import synthetic_pulse_waveform


class FakeDiagnosisService:
    def __init__(self):
        from tcm_ai.services.diagnosis_service import DiagnosisService

        self._inner = DiagnosisService(tcm_agent=MagicMock())

    @property
    def tcm_agent(self):
        return self._inner.tcm_agent

    def analyze_pulse_request(self, payload):
        result = self._inner.analyze_pulse_request(payload)
        agent = self.tcm_agent
        agent._search_related_knowledge.return_value = []
        return result


@pytest.fixture
def client():
    app = create_app()
    app.dependency_overrides[get_diagnosis_service] = lambda: FakeDiagnosisService()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_pulse_analyze_api(client):
    samples = synthetic_pulse_waveform(duration_sec=20.0, fs=100.0, bpm=70.0)
    resp = client.post(
        "/api/pulse/analyze",
        json={"samples": samples, "fs": 100.0, "source": "test"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["pulse_type"] in {"平和脉", "迟脉", "数脉", "不齐脉"}
    assert body["research_features"]["systolic_amplitude"] > 0
    assert body["characteristics"]["depth"] is None


def test_pulse_analyze_rejects_short_sample(client):
    resp = client.post("/api/pulse/analyze", json={"samples": [1, 2, 3], "fs": 100.0})
    assert resp.status_code == 422


def test_pulse_session_stores_jsonl(client, monkeypatch, tmp_path):
    sessions_path = tmp_path / "pulse_sessions.jsonl"
    monkeypatch.setattr("tcm_ai.api.routes.pulse.SESSIONS_PATH", str(sessions_path))

    samples = synthetic_pulse_waveform(duration_sec=20.0, fs=100.0, bpm=70.0)
    resp = client.post(
        "/api/pulse/sessions",
        json={"samples": samples, "fs": 100.0, "source": "test"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["stored"] is True
    assert body["session_id"]

    lines = sessions_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["session_id"] == body["session_id"]
    assert record["result"]["success"] is True
