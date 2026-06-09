# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""Prometheus 文本格式指标（供 scrape）。"""

from __future__ import annotations

import os
import secrets
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from tcm_ai.core.redis_client import redis_url
from tcm_ai.core.request_metrics import format_prometheus_counters
from tcm_ai.core.runtime import get_tcm_env, is_production
from tcm_ai.core.startup import check_python_packages, index_ready

router = APIRouter(tags=["监控"])

_started_at = time.time()


def _metrics_token() -> str:
    return (os.environ.get("TCM_METRICS_TOKEN") or "").strip()


def _authorize_metrics(request: Request) -> None:
    expected = _metrics_token()
    if not expected:
        return
    auth = (request.headers.get("authorization") or "").strip()
    token: Optional[str] = None
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    if not token or not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="metrics unauthorized")


def _line(name: str, value: float | int, mtype: str, help_text: str) -> list[str]:
    return [
        f"# HELP {name} {help_text}",
        f"# TYPE {name} {mtype}",
        f"{name} {value}",
    ]


@router.get("/metrics")
def prometheus_metrics(request: Request) -> PlainTextResponse:
    _authorize_metrics(request)
    missing = check_python_packages()
    lines: list[str] = []
    lines.extend(_line("tcm_uptime_seconds", round(time.time() - _started_at, 1), "gauge", "Process uptime"))
    lines.extend(_line("tcm_index_ready", 1 if index_ready() else 0, "gauge", "Vector index ready"))
    lines.extend(_line("tcm_rag_deps_ok", 1 if not missing else 0, "gauge", "RAG dependencies satisfied"))
    lines.extend(_line("tcm_production_mode", 1 if is_production() else 0, "gauge", "Production mode"))
    lines.extend(_line("tcm_redis_rate_limit", 1 if redis_url() else 0, "gauge", "Redis rate limit enabled"))
    lines.extend(format_prometheus_counters())
    lines.append(f'tcm_env{{env="{get_tcm_env()}"}} 1')
    body = "\n".join(lines) + "\n"
    return PlainTextResponse(content=body, media_type="text/plain; version=0.0.4; charset=utf-8")
