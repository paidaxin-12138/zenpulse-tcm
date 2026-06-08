import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tcm_ai.api.deps import get_index_rebuild_service
from tcm_ai.api.routes.admin import require_admin_key, require_editor, router as admin_router


class FakeRebuildService:
    def __init__(self):
        self.started = False

    def start(self, force=False):
        self.started = True
        return {
            "job_id": "job-test",
            "status": "running",
            "progress": 0,
            "phase": "starting",
            "message": "任务已启动",
            "force": force,
        }

    def get_status(self):
        if self.started:
            return {
                "job_id": "job-test",
                "status": "running",
                "progress": 55,
                "phase": "embedding",
                "message": "向量化批次 2/4",
            }
        return {"status": "idle", "progress": 0}


@pytest.fixture
def client():
    fake = FakeRebuildService()
    app = FastAPI()
    app.include_router(admin_router)
    app.dependency_overrides[require_admin_key] = lambda: "admin"
    app.dependency_overrides[require_editor] = lambda: "admin"
    app.dependency_overrides[get_index_rebuild_service] = lambda: fake
    with TestClient(app) as test_client:
        yield test_client, fake
    app.dependency_overrides.clear()


def test_async_rebuild_and_status(client):
    test_client, fake = client
    resp = test_client.post("/api/admin/rag/rebuild-index/async?force=true")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "running"
    assert fake.started

    status_resp = test_client.get("/api/admin/rag/rebuild-index/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["progress"] == 55
