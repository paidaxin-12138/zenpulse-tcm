# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from tcm_ai.core.config_store import load_config
from tcm_ai.core.paths import VECTOR_INDEX_PATH
from tcm_ai.core.url_safety import UnsafeUrlError, validate_outbound_base_url


def _index_ready(index_path: str) -> bool:
    if not os.path.isdir(index_path):
        return False
    return any(
        name.endswith(".sqlite3") or name == "chroma.sqlite3"
        for name in os.listdir(index_path)
    )

_SAMPLE_RERANK_DOCS = [
    {"content": "气血不足常见面色苍白、舌质淡、神疲乏力。", "title": "气血"},
    {"content": "肝阳上亢可见头痛眩晕、面红目赤、脉弦。", "title": "肝阳"},
    {"content": "痰湿内阻多表现为舌苔厚腻、胸闷纳呆。", "title": "痰湿"},
]


def _merge_provider_cfg(section: str, override: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    config = load_config()
    cfg = dict(config[section])
    if override:
        for key, value in override.items():
            if value is not None and value != "":
                cfg[key] = value
    base_url = (cfg.get("base_url") or "").strip()
    if base_url and cfg.get("provider") in ("openai", "ollama", "api"):
        try:
            cfg["base_url"] = validate_outbound_base_url(base_url)
        except UnsafeUrlError as exc:
            raise ValueError(str(exc)) from exc
    return cfg


class SystemService:
    def index_status(self) -> Dict[str, Any]:
        config = load_config()
        exists = _index_ready(VECTOR_INDEX_PATH)
        status: Dict[str, Any] = {
            "index_path": VECTOR_INDEX_PATH,
            "exists": exists,
            "embedding_provider": config["embedding"]["provider"],
            "embedding_model": config["embedding"]["model"],
            "llm_provider": config["llm"]["provider"],
            "llm_model": config["llm"]["model"],
            "rerank_provider": config["rerank"]["provider"],
        }
        if exists:
            mtime = os.path.getmtime(VECTOR_INDEX_PATH)
            status["last_modified"] = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
            try:
                from tcm_ai.rag.vector_index import VectorIndexService

                store = VectorIndexService().get_store()
                status["document_count"] = store._collection.count()
            except Exception as exc:
                status["document_count"] = None
                status["count_error"] = str(exc)
        return status

    def test_embedding(self, override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        from tcm_ai.rag.providers import create_embeddings

        cfg = _merge_provider_cfg("embedding", override)
        try:
            emb = create_embeddings(cfg)
            vec = emb.embed_query("中医测试")
            return {
                "ok": True,
                "dimensions": len(vec) if vec else 0,
                "provider": cfg.get("provider"),
                "model": cfg.get("model"),
            }
        except Exception as exc:
            return {"ok": False, "provider": cfg.get("provider"), "error": str(exc)}

    def test_llm(self, override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        from tcm_ai.rag.providers import invoke_llm

        cfg = _merge_provider_cfg("llm", override)
        try:
            answer = invoke_llm(cfg, "请只回复：连通正常")
            result: Dict[str, Any] = {
                "ok": bool(answer and answer.strip()),
                "preview": (answer or "")[:100],
                "provider": cfg.get("provider"),
                "model": cfg.get("model"),
            }
            if cfg.get("provider") == "ollama":
                base = (cfg.get("base_url") or "http://127.0.0.1:11434").rstrip("/")
                try:
                    resp = httpx.get(f"{base}/api/tags", timeout=10.0)
                    result["ollama_reachable"] = resp.status_code == 200
                except Exception as exc:
                    result["ollama_reachable"] = False
                    result["ollama_error"] = str(exc)
            return result
        except Exception as exc:
            return {"ok": False, "provider": cfg.get("provider"), "error": str(exc)}

    def test_rerank(self, override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cfg = _merge_provider_cfg("rerank", override)
        provider = cfg.get("provider", "none")
        if provider == "none":
            return {"ok": True, "skipped": True, "message": "Rerank 已禁用（provider=none）"}
        from tcm_ai.rag.providers import rerank_documents

        try:
            ranked = rerank_documents(cfg, "气血不足", _SAMPLE_RERANK_DOCS, top_n=2)
            return {
                "ok": len(ranked) > 0,
                "provider": provider,
                "model": cfg.get("model"),
                "top_title": ranked[0].get("title") if ranked else None,
                "top_score": ranked[0].get("rerank_score") if ranked else None,
            }
        except Exception as exc:
            return {"ok": False, "provider": provider, "error": str(exc)}

    def test_models(
        self,
        embedding: Optional[Dict[str, Any]] = None,
        llm: Optional[Dict[str, Any]] = None,
        rerank: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        results: Dict[str, Any] = {
            "embedding": self.test_embedding(embedding),
            "llm": self.test_llm(llm),
            "rerank": self.test_rerank(rerank),
        }
        if results["llm"].get("provider") == "ollama":
            base = (load_config()["llm"].get("base_url") or "http://127.0.0.1:11434").rstrip("/")
            try:
                resp = httpx.get(f"{base}/api/tags", timeout=10.0)
                results["ollama"] = {"ok": resp.status_code == 200, "status_code": resp.status_code}
            except Exception as exc:
                results["ollama"] = {"ok": False, "error": str(exc)}

        results["all_ok"] = all(
            item.get("ok") or item.get("skipped")
            for item in results.values()
            if isinstance(item, dict)
        )
        return results
