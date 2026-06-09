# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""进程内滑动窗口限流；可选 Redis（TCM_REDIS_URL）跨 worker 共享。"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from threading import Lock
from typing import DefaultDict, List, Optional

from fastapi import HTTPException, Request

from tcm_ai.core.redis_client import get_redis, redis_url
from tcm_ai.core.runtime import is_production
from tcm_ai.core.settings import get_settings

logger = logging.getLogger(__name__)

_lock = Lock()
_buckets: DefaultDict[str, List[float]] = defaultdict(list)


def client_ip(request: Request) -> str:
    """生产环境优先使用反代设置的 X-Forwarded-For 首段。"""
    if is_production():
        forwarded = (request.headers.get("x-forwarded-for") or "").strip()
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = (request.headers.get("x-real-ip") or "").strip()
        if real_ip:
            return real_ip
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


_redis_fallback_logged = False


def redis_configured() -> bool:
    return bool(redis_url())


def redis_degraded() -> bool:
    """TCM_REDIS_URL 已设置但当前无法使用 Redis。"""
    return redis_configured() and get_redis() is None


def _check_rate_limit_redis(key: str, limit: int, window_seconds: float) -> None:
    client = get_redis()
    if not client:
        return
    pipe = client.pipeline()
    pipe.incr(key)
    pipe.expire(key, max(1, int(window_seconds)))
    count, _ = pipe.execute()
    if int(count) > limit:
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")


def _log_redis_rate_limit_fallback(scope: str) -> None:
    global _redis_fallback_logged
    if _redis_fallback_logged:
        return
    _redis_fallback_logged = True
    msg = (
        f"TCM_REDIS_URL 已配置但 Redis 不可用，限流 scope={scope} 回退进程内内存"
        "（多 worker 下各进程独立计数）"
    )
    if is_production():
        logger.error(msg)
    else:
        logger.warning(msg)


def check_rate_limit(
    request: Request,
    *,
    scope: str,
    limit: int,
    window_seconds: float = 60.0,
) -> None:
    if limit <= 0:
        return
    ip = client_ip(request)
    key = f"tcm:rl:{scope}:{ip}"
    if redis_url():
        try:
            client = get_redis()
            if client:
                _check_rate_limit_redis(key, limit, window_seconds)
                return
            _log_redis_rate_limit_fallback(scope)
        except HTTPException:
            raise
        except Exception as exc:
            if is_production():
                logger.error("Redis 限流失败，回退内存: %s", exc)
            else:
                logger.warning("Redis 限流失败，回退内存: %s", exc)
    now = time.time()
    mem_key = key
    with _lock:
        bucket = [t for t in _buckets[mem_key] if now - t < window_seconds]
        if len(bucket) >= limit:
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
        bucket.append(now)
        _buckets[mem_key] = bucket


def check_public_rate_limit(
    request: Request,
    *,
    scope: str,
    default_limit: Optional[int] = None,
) -> None:
    cfg = get_settings().get("server") or {}
    limit = int(cfg.get("rate_limit_per_minute") or default_limit or 60)
    check_rate_limit(request, scope=scope, limit=limit)


def check_admin_auth_rate_limit(request: Request) -> None:
    """管理端鉴权失败 brute-force 防护（默认 20 次/分钟/IP）。"""
    check_rate_limit(request, scope="admin_auth_fail", limit=20)


def reset_redis_rate_limit_state_for_tests() -> None:
    global _redis_fallback_logged
    _redis_fallback_logged = False
    with _lock:
        _buckets.clear()


def clear_admin_auth_rate_limit(request: Request) -> None:
    ip = client_ip(request)
    key = f"tcm:rl:admin_auth_fail:{ip}"
    client = get_redis()
    if client:
        try:
            client.delete(key)
        except Exception:
            pass
    with _lock:
        _buckets.pop(key, None)
