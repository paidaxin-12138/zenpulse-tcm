# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import json
from pathlib import Path

import tcm_ai.core.config_store as config_store_module
import tcm_ai.services.rag_log_service as rag_log_module
from fastapi.testclient import TestClient

from tcm_ai.api.app import create_app


def _prod_config():
    return {
        "admin_api_key": "test-admin-key-thirty-two-chars-min",
        "server": {
            "cors_origins": ["https://example.com"],
            "allow_public_diagnose": False,
            "allow_public_knowledge_search": False,
        },
        "wechat_miniprogram": {"dev_mode": False, "token_secret": "wx-prod-token-" + "a" * 18},
        "embedding": {"provider": "local", "model": "m", "base_url": "", "api_key": ""},
        "llm": {"provider": "ollama", "model": "m", "base_url": "http://127.0.0.1:11434", "api_key": ""},
        "rerank": {"provider": "none", "model": "", "base_url": "", "api_key": ""},
        "rag": {"rebuild_on_missing_index": False},
        "rbac": {"enabled": False, "keys": []},
    }


def test_full_app_starts_in_production(monkeypatch, tmp_path):
    monkeypatch.setenv("TCM_ENV", "production")
    cfg_path = tmp_path / "admin_config.json"
    cfg_path.write_text(json.dumps(_prod_config()), encoding="utf-8")
    monkeypatch.setattr(config_store_module, "ADMIN_CONFIG_PATH", str(cfg_path))
    monkeypatch.setattr(config_store_module, "DATA_DIR", str(tmp_path))

    with TestClient(create_app()) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        ready = client.get("/api/ready")
        assert ready.status_code == 200
        assert ready.json()["ready"] is True


def test_admin_has_security_headers(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "development")
    with TestClient(create_app()) as client:
        res = client.get("/admin")
        assert res.status_code == 200
        assert res.headers.get("X-Content-Type-Options") == "nosniff"
        assert "Content-Security-Policy" in res.headers


def test_rag_log_redacts_question_in_production(monkeypatch, tmp_path):
    monkeypatch.setenv("TCM_ENV", "production")
    log_path = tmp_path / "rag_logs.jsonl"
    monkeypatch.setattr(rag_log_module, "RAG_LOG_PATH", str(log_path))
    monkeypatch.setattr(rag_log_module, "DATA_DIR", str(tmp_path))

    from tcm_ai.services.rag_log_service import log_rag_event

    log_rag_event(
        "query",
        "患者隐私问题内容",
        source="admin",
        providers={"embedding": "http://127.0.0.1:11434", "llm": "deepseek"},
        answer_preview="含隐私的回答摘要",
    )
    line = Path(log_path).read_text(encoding="utf-8").strip()
    record = json.loads(line)
    assert record["question"].startswith("[redacted:")
    assert "患者" not in record["question"]
    assert record["answer_preview"] == ""
    assert record["providers"]["embedding"] == "[redacted]"
    assert record["providers"]["llm"] == "[redacted]"
