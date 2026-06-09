# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import os
import shutil
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

ProgressCallback = Callable[[Dict[str, Any]], None]

EMBED_BATCH_SIZE = 32


class IndexRebuildService:
    """后台向量索引重建任务（单例，进程内）。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._status: Dict[str, Any] = self._idle_status()

    @staticmethod
    def _idle_status() -> Dict[str, Any]:
        return {
            "job_id": None,
            "status": "idle",
            "phase": "",
            "progress": 0,
            "message": "",
            "chunks": None,
            "index_path": None,
            "error": None,
            "force": False,
            "started_at": None,
            "finished_at": None,
        }

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._status)

    def start(self, force: bool = False) -> Dict[str, Any]:
        with self._lock:
            if self._status["status"] == "running":
                raise RuntimeError("已有索引重建任务进行中")
            job_id = uuid.uuid4().hex[:12]
            self._status = {
                **self._idle_status(),
                "job_id": job_id,
                "status": "running",
                "phase": "starting",
                "progress": 0,
                "message": "任务已启动",
                "force": force,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
            self._thread = threading.Thread(
                target=self._run,
                args=(force, job_id),
                daemon=True,
                name="index-rebuild",
            )
            self._thread.start()
            return dict(self._status)

    def _update(self, **fields: Any) -> None:
        with self._lock:
            self._status.update(fields)

    def _on_progress(self, payload: Dict[str, Any]) -> None:
        self._update(
            phase=payload.get("phase", ""),
            progress=int(payload.get("progress", 0)),
            message=payload.get("message", ""),
        )

    def _run(self, force: bool, job_id: str) -> None:
        try:
            from tcm_ai.core.service_registry import get_rag_pipeline, reset_ai_cache

            pipeline = get_rag_pipeline()
            pipeline.vector_index.invalidate()
            result = pipeline.vector_index.build_index(
                force=force,
                progress_callback=self._on_progress,
                batch_size=EMBED_BATCH_SIZE,
            )
            reset_ai_cache()
            self._update(
                status="completed",
                phase="completed",
                progress=100,
                message=f"索引重建完成，共 {result['chunks']} 个分块",
                chunks=result.get("chunks"),
                index_path=result.get("index_path"),
                finished_at=datetime.now(timezone.utc).isoformat(),
                error=None,
            )
        except Exception as exc:
            self._update(
                status="failed",
                phase="failed",
                message="索引重建失败",
                error=str(exc),
                finished_at=datetime.now(timezone.utc).isoformat(),
            )
