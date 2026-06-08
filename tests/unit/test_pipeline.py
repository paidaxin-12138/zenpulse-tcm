import sys
import types
from unittest.mock import MagicMock

import pytest

from tcm_ai.rag.pipeline import RAGPipeline

_MOCK_CONFIG = {
    "embedding": {"provider": "local", "model": "m"},
    "llm": {"provider": "ollama", "model": "m", "base_url": "", "api_key": "", "temperature": 0.3},
    "rerank": {"provider": "none", "model": "", "base_url": "", "api_key": "", "top_n": 5},
    "rag": {"retrieval_top_k": 5, "final_top_k": 2, "enable_llm_answer": True},
}


@pytest.fixture
def pipeline():
    p = RAGPipeline.__new__(RAGPipeline)
    p.vector_index = MagicMock()
    return p


@pytest.fixture
def mock_providers(monkeypatch):
    mod = types.ModuleType("tcm_ai.rag.providers")
    mod.rerank_documents = lambda _c, _q, docs, top_n: docs[:top_n]
    mod.invoke_llm = lambda _c, _p: "回答"
    monkeypatch.setitem(sys.modules, "tcm_ai.rag.providers", mod)
    return mod


def test_search_knowledge_returns_reranked(pipeline, mock_providers, monkeypatch):
    pipeline.vector_index.search.return_value = [{"content": "c1", "title": "t1", "score": 0.1}]
    monkeypatch.setattr("tcm_ai.rag.pipeline.load_config", lambda: _MOCK_CONFIG)
    with monkeypatch.context() as m:
        m.setattr("tcm_ai.rag.pipeline.log_rag_event", lambda *a, **k: None)
        results = pipeline.search_knowledge("气血", top_k=1, source="test")
    assert len(results) == 1
    assert results[0]["title"] == "t1"


def test_query_skips_llm_when_no_context(pipeline, mock_providers, monkeypatch):
    calls = {"llm": 0}
    mock_providers.invoke_llm = lambda *_: calls.__setitem__("llm", calls["llm"] + 1) or "x"
    pipeline.vector_index.search.return_value = []
    mock_providers.rerank_documents = lambda _c, _q, docs, top_n: []
    monkeypatch.setattr("tcm_ai.rag.pipeline.load_config", lambda: _MOCK_CONFIG)
    monkeypatch.setattr("tcm_ai.rag.pipeline.log_rag_event", lambda *a, **k: None)
    result = pipeline.query("问题", enable_llm_answer=True)
    assert calls["llm"] == 0
    assert "未检索到" in result["answer"]


def test_query_calls_llm_with_context(pipeline, mock_providers, monkeypatch):
    calls = {"llm": 0}
    mock_providers.invoke_llm = lambda *_: calls.__setitem__("llm", calls["llm"] + 1) or "回答"
    docs = [{"content": "内容", "title": "标题", "file_path": "a.txt", "category": "理论", "score": 0.2}]
    pipeline.vector_index.search.return_value = docs
    mock_providers.rerank_documents = lambda _c, _q, d, top_n: d[:top_n]
    monkeypatch.setattr("tcm_ai.rag.pipeline.load_config", lambda: _MOCK_CONFIG)
    monkeypatch.setattr("tcm_ai.rag.pipeline.log_rag_event", lambda *a, **k: None)
    result = pipeline.query("问题", enable_llm_answer=True)
    assert calls["llm"] == 1
    assert result["answer"] == "回答"
