from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tcm_ai.api.deps import get_rag_pipeline
from tcm_ai.api.routes.knowledge import router as knowledge_router


class FakePipeline:
    def search_knowledge(self, query, top_k=5, source="public"):
        return [{"title": "测试", "content": f"关于{query}", "score": 0.1}]


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(knowledge_router)
    app.dependency_overrides[get_rag_pipeline] = lambda: FakePipeline()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_public_knowledge_search(client):
    resp = client.post("/api/knowledge/search", json={"query": "气血", "top_k": 3})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["query"] == "气血"
    assert len(body["results"]) == 1
