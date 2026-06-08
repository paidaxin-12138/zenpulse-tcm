"""公开 API 访问控制与简易限流。"""

from __future__ import annotations

from fastapi import HTTPException, Request

from tcm_ai.core.rate_limit import check_public_rate_limit
from tcm_ai.core.runtime import is_production
from tcm_ai.core.settings import get_settings


def _server_cfg() -> dict:
    return get_settings().get("server") or {}


def ensure_public_diagnose_allowed(request: Request) -> None:
    cfg = _server_cfg()
    if is_production() and not cfg.get("allow_public_diagnose", False):
        raise HTTPException(
            status_code=403,
            detail="生产环境已关闭公开诊断接口，请使用微信小程序或联系管理员开启",
        )
    check_public_rate_limit(request, scope="diagnose")


def ensure_public_knowledge_search_allowed(request: Request) -> None:
    cfg = _server_cfg()
    if is_production() and not cfg.get("allow_public_knowledge_search", False):
        raise HTTPException(status_code=403, detail="生产环境已关闭公开知识检索")
    check_public_rate_limit(request, scope="knowledge")


def ensure_wx_login_allowed(request: Request) -> None:
    check_public_rate_limit(request, scope="wx_login", default_limit=30)
