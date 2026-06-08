"""对外 HTTP 错误消息（避免泄露内部异常细节）。"""

from __future__ import annotations

import logging

from tcm_ai.core.runtime import is_production

logger = logging.getLogger(__name__)


def safe_client_message(
    exc: BaseException,
    *,
    public: str,
    dev_prefix: str = "",
) -> str:
    """生产环境返回通用文案；开发环境可附带异常类型便于调试。"""
    logger.exception("%s: %s", public, exc)
    if is_production():
        return public
    detail = f"{type(exc).__name__}: {exc}"
    return f"{dev_prefix}{detail}" if dev_prefix else detail
