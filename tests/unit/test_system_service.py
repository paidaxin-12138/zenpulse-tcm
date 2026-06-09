# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import pytest

from tcm_ai.services.system_service import SystemService


def test_rerank_skip_when_none(monkeypatch):
    monkeypatch.setattr(
        "tcm_ai.services.system_service.load_config",
        lambda: {
            "embedding": {"provider": "local", "model": "m", "base_url": "", "api_key": ""},
            "llm": {"provider": "ollama", "model": "m", "base_url": "", "api_key": "", "temperature": 0.3},
            "rerank": {"provider": "none", "model": "", "base_url": "", "api_key": "", "top_n": 5},
        },
    )
    result = SystemService().test_rerank()
    assert result["skipped"] is True
    assert result["ok"] is True


def test_merge_provider_cfg_uses_override(monkeypatch):
    from tcm_ai.services.system_service import _merge_provider_cfg

    monkeypatch.setattr(
        "tcm_ai.services.system_service.load_config",
        lambda: {
            "embedding": {"provider": "local", "model": "saved", "base_url": "", "api_key": "secret"},
        },
    )
    cfg = _merge_provider_cfg("embedding", {"model": "new-model", "api_key": ""})
    assert cfg["model"] == "new-model"
    assert cfg["api_key"] == "secret"
