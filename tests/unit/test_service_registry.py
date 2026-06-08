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
