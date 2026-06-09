# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""进程内 HTTP 请求计数（Prometheus counter）。"""

from __future__ import annotations

import re
from threading import Lock
from typing import DefaultDict, Dict, Iterable, Tuple

_lock = Lock()
_counters: DefaultDict[Tuple[str, str, str], int] = DefaultDict(int)

_SKIP_PREFIXES = (
    "/metrics",
    "/admin-static",
    "/assets",
    "/static",
    "/favicon.ico",
)

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.I,
)


def normalize_path(path: str) -> str:
    if not path or path == "/":
        return "/"
    parts = [p for p in path.split("/") if p]
    normalized: list[str] = []
    for part in parts:
        if part.isdigit() or _UUID_RE.match(part):
            normalized.append("{id}")
        else:
            normalized.append(part)
    return "/" + "/".join(normalized)


def should_record_path(path: str) -> bool:
    if not path:
        return False
    for prefix in _SKIP_PREFIXES:
        if path == prefix or path.startswith(prefix + "/"):
            return False
    return True


def record_request(method: str, path: str, status_code: int) -> None:
    if not should_record_path(path):
        return
    route = normalize_path(path)
    key = (method.upper(), route, str(status_code))
    with _lock:
        _counters[key] += 1


def snapshot_counters() -> Dict[Tuple[str, str, str], int]:
    with _lock:
        return dict(_counters)


def format_prometheus_counters() -> Iterable[str]:
    lines = [
        "# HELP tcm_http_requests_total Total HTTP requests",
        "# TYPE tcm_http_requests_total counter",
    ]
    for (method, route, status), count in sorted(snapshot_counters().items()):
        safe_route = route.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(
            f'tcm_http_requests_total{{method="{method}",route="{safe_route}",status="{status}"}} {count}'
        )
    return lines


def reset_counters_for_tests() -> None:
    with _lock:
        _counters.clear()
