# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import pytest

from tcm_ai.services.rag_log_service import RAGLogService, log_rag_event


@pytest.fixture
def log_path(tmp_path, monkeypatch):
    path = tmp_path / "rag_logs.jsonl"
    monkeypatch.setattr("tcm_ai.services.rag_log_service.RAG_LOG_PATH", str(path))
    monkeypatch.setattr("tcm_ai.services.rag_log_service.DATA_DIR", str(tmp_path))
    return path


def test_append_and_list_logs(log_path) -> None:
    svc = RAGLogService()
    log_rag_event("query", "测试问题", retrieved_count=3, has_answer=True, answer_preview="回答")
    result = svc.list_logs(limit=10)
    assert result["total"] == 1
    assert result["logs"][0]["kind"] == "query"
    assert result["logs"][0]["question"] == "测试问题"


def test_clear_logs(log_path) -> None:
    svc = RAGLogService()
    log_rag_event("search", "检索", retrieved_count=1)
    svc.clear()
    assert svc.list_logs()["total"] == 0


def test_list_logs_filter_by_source(log_path) -> None:
    log_rag_event("search", "admin q", source="admin")
    log_rag_event("search", "diag q", source="diagnosis")
    svc = RAGLogService()
    filtered = svc.list_logs(limit=10, source="diagnosis")
    assert filtered["total"] == 1
    assert filtered["logs"][0]["source"] == "diagnosis"


def test_list_logs_filter_by_kind(log_path) -> None:
    log_rag_event("query", "q1", source="admin")
    log_rag_event("search", "q2", source="admin")
    svc = RAGLogService()
    filtered = svc.list_logs(limit=10, kind="search")
    assert filtered["total"] == 1
    assert filtered["logs"][0]["kind"] == "search"


def test_stats_aggregation(log_path) -> None:
    log_rag_event("search", "s1", source="diagnosis", duration_ms=100)
    log_rag_event("query", "q1", source="admin", duration_ms=200, has_answer=True)
    log_rag_event("query", "q2", source="admin", duration_ms=300, has_answer=False)
    svc = RAGLogService()
    stats = svc.stats()
    assert stats["total"] == 3
    assert stats["by_source"]["diagnosis"] == 1
    assert stats["by_source"]["admin"] == 2
    assert stats["avg_duration_ms"] == 200.0
    assert stats["llm_answer_rate"] == 0.5
    assert len(stats["recent"]) == 3


def test_trim_old_entries(log_path, monkeypatch) -> None:
    monkeypatch.setattr("tcm_ai.services.rag_log_service.MAX_ENTRIES", 3)
    svc = RAGLogService()
    for i in range(5):
        log_rag_event("search", f"q{i}", retrieved_count=1)
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 3
    latest = svc.list_logs(limit=1)["logs"][0]
    assert latest["question"] == "q4"
