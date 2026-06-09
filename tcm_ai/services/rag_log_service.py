# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import hashlib

from tcm_ai.core.runtime import is_production
from tcm_ai.core.paths import DATA_DIR

RAG_LOG_PATH = os.path.join(DATA_DIR, "rag_logs.jsonl")
MAX_ENTRIES = 500
_lock = threading.Lock()


class RAGLogService:
    def append(self, entry: Dict[str, Any]) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **entry,
        }
        os.makedirs(DATA_DIR, exist_ok=True)
        with _lock:
            with open(RAG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            self._trim_file()

    def _trim_file(self) -> None:
        if not os.path.isfile(RAG_LOG_PATH):
            return
        with open(RAG_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) <= MAX_ENTRIES:
            return
        trimmed = lines[-MAX_ENTRIES:]
        tmp_path = RAG_LOG_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.writelines(trimmed)
        os.replace(tmp_path, RAG_LOG_PATH)

    def list_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        source: Optional[str] = None,
        kind: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not os.path.isfile(RAG_LOG_PATH):
            return {
                "total": 0,
                "offset": offset,
                "limit": limit,
                "source": source,
                "kind": kind,
                "logs": [],
            }
        with _lock:
            with open(RAG_LOG_PATH, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
        entries: List[Dict[str, Any]] = []
        for line in reversed(lines):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if source and entry.get("source") != source:
                continue
            if kind and entry.get("kind") != kind:
                continue
            entries.append(entry)
        total = len(entries)
        page = entries[offset : offset + limit]
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "source": source,
            "kind": kind,
            "logs": page,
        }

    def clear(self) -> Dict[str, str]:
        with _lock:
            if os.path.isfile(RAG_LOG_PATH):
                os.remove(RAG_LOG_PATH)
        return {"cleared": "ok"}

    def stats(self) -> Dict[str, Any]:
        if not os.path.isfile(RAG_LOG_PATH):
            return {
                "total": 0,
                "by_source": {},
                "by_kind": {},
                "avg_duration_ms": 0,
                "llm_answer_rate": 0,
                "recent": [],
            }
        with _lock:
            with open(RAG_LOG_PATH, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

        entries: List[Dict[str, Any]] = []
        for line in lines:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        by_source: Dict[str, int] = {}
        by_kind: Dict[str, int] = {}
        durations: List[float] = []
        query_total = 0
        query_with_answer = 0

        for entry in entries:
            src = entry.get("source", "unknown")
            kind = entry.get("kind", "unknown")
            by_source[src] = by_source.get(src, 0) + 1
            by_kind[kind] = by_kind.get(kind, 0) + 1
            if entry.get("duration_ms") is not None:
                durations.append(float(entry["duration_ms"]))
            if kind == "query":
                query_total += 1
                if entry.get("has_answer"):
                    query_with_answer += 1

        recent = list(reversed(entries))[:5]
        return {
            "total": len(entries),
            "by_source": by_source,
            "by_kind": by_kind,
            "avg_duration_ms": round(sum(durations) / len(durations), 2) if durations else 0,
            "llm_answer_rate": round(query_with_answer / query_total, 4) if query_total else 0,
            "recent": recent,
        }


def _sanitize_question(question: str) -> str:
    text = (question or "").strip()
    if not text:
        return ""
    if is_production():
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
        return f"[redacted:{digest}]"
    return text[:500]


def _sanitize_providers(providers: Optional[Dict[str, str]]) -> Dict[str, str]:
    raw = providers or {}
    if not is_production():
        return dict(raw)
    return {key: "[redacted]" for key in raw}


def _sanitize_answer_preview(answer_preview: str) -> str:
    if is_production():
        return ""
    return (answer_preview or "")[:200]


def log_rag_event(
    kind: str,
    question: str,
    *,
    retrieved_count: int = 0,
    final_top_k: int = 0,
    providers: Optional[Dict[str, str]] = None,
    duration_ms: float = 0,
    has_answer: bool = False,
    answer_preview: str = "",
    source: str = "system",
) -> None:
    RAGLogService().append(
        {
            "kind": kind,
            "question": _sanitize_question(question),
            "retrieved_count": retrieved_count,
            "final_top_k": final_top_k,
            "providers": _sanitize_providers(providers),
            "duration_ms": round(duration_ms, 2),
            "has_answer": has_answer,
            "answer_preview": _sanitize_answer_preview(answer_preview),
            "source": source,
        }
    )
