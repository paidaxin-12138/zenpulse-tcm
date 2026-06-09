# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from tcm_ai.core.service_registry import reset_ai_cache


def test_service_registry_reset_clears_pipeline(monkeypatch):
    import tcm_ai.core.service_registry as registry

    class FakeIndex:
        invalidated = False

        def invalidate(self):
            self.invalidated = True

    class FakePipeline:
        def __init__(self):
            self.vector_index = FakeIndex()

    fake = FakePipeline()
    monkeypatch.setattr(registry, "_rag_pipeline", fake)
    reset_ai_cache()
    assert fake.vector_index.invalidated
    assert registry._rag_pipeline is None
