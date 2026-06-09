# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import threading
import time

import pytest

from tcm_ai.services.index_rebuild_service import IndexRebuildService


def test_get_status_idle():
    service = IndexRebuildService()
    status = service.get_status()
    assert status["status"] == "idle"
    assert status["progress"] == 0


def test_on_progress_updates_status():
    service = IndexRebuildService()
    service._update(status="running", progress=0, message="")
    service._on_progress({"phase": "embedding", "progress": 42, "message": "向量化中"})
    status = service.get_status()
    assert status["progress"] == 42
    assert status["phase"] == "embedding"
    assert status["message"] == "向量化中"


def test_start_rejects_when_running():
    service = IndexRebuildService()
    started = threading.Event()

    def slow_run(force, job_id):
        started.set()
        time.sleep(0.3)

    service._run = slow_run  # type: ignore[method-assign]
    service.start(force=True)
    assert started.wait(timeout=1)
    with pytest.raises(RuntimeError, match="进行中"):
        service.start(force=True)


def test_run_completes_with_mock_pipeline(monkeypatch):
    service = IndexRebuildService()

    class FakeVectorIndex:
        def invalidate(self):
            pass

        def build_index(self, force=False, progress_callback=None, batch_size=32):
            if progress_callback:
                progress_callback({"phase": "completed", "progress": 100, "message": "ok"})
            return {"chunks": 8, "index_path": "/tmp/x"}

    class FakePipeline:
        vector_index = FakeVectorIndex()

    import tcm_ai.core.service_registry as registry

    monkeypatch.setattr(registry, "get_rag_pipeline", lambda: FakePipeline())
    monkeypatch.setattr(registry, "reset_ai_cache", lambda: None)

    service._run(force=True, job_id="test-job")
    status = service.get_status()
    assert status["status"] == "completed"
    assert status["chunks"] == 8
    assert status["progress"] == 100
