import logging

from fastapi import Request

import tcm_ai.core.redis_client as redis_client_module
from tcm_ai.core.rate_limit import check_rate_limit, reset_redis_rate_limit_state_for_tests


def _request() -> Request:
    scope = {"type": "http", "headers": [], "client": ("127.0.0.1", 12345)}
    return Request(scope)


def test_redis_fallback_logs_when_configured_but_unavailable(monkeypatch, caplog):
    monkeypatch.setenv("TCM_REDIS_URL", "redis://127.0.0.1:9/0")
    monkeypatch.setenv("TCM_ENV", "production")
    reset_redis_rate_limit_state_for_tests()
    redis_client_module.reset_redis_client_for_tests()
    monkeypatch.setattr(redis_client_module, "_redis_unavailable", True)

    caplog.set_level(logging.ERROR)
    check_rate_limit(_request(), scope="test_scope", limit=100)
    assert any("Redis 不可用" in r.message for r in caplog.records)
