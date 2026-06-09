# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""可选 Redis 连接（限流、Admin 会话黑名单等共享）。"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_redis_client = None
_redis_unavailable = False


def redis_url() -> str:
    return (os.environ.get("TCM_REDIS_URL") or "").strip()


def get_redis():
    global _redis_client, _redis_unavailable
    if _redis_unavailable or not redis_url():
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        import redis

        _redis_client = redis.from_url(redis_url(), decode_responses=True)
        _redis_client.ping()
        logger.info("Redis 已连接: %s", redis_url().split("@")[-1])
        return _redis_client
    except Exception as exc:
        logger.warning("Redis 不可用: %s", exc)
        _redis_unavailable = True
        return None


def reset_redis_client_for_tests() -> None:
    """测试用：重置连接状态。"""
    global _redis_client, _redis_unavailable
    _redis_client = None
    _redis_unavailable = False
