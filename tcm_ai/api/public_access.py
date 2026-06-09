"""公开 API 访问控制与简易限流。"""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, Request

from tcm_ai.core.rate_limit import check_public_rate_limit
from tcm_ai.core.runtime import is_production
from tcm_ai.core.settings import get_settings


def _server_cfg() -> dict:
    return get_settings().get("server") or {}


def _ensure_authenticated_or_public(
    request: Request,
    wx_user_id: Optional[str],
    *,
    public_flag: str,
    scope: str,
    closed_detail: str,
) -> None:
    if wx_user_id:
        check_public_rate_limit(request, scope=scope)
        return
    cfg = _server_cfg()
    if is_production() and not cfg.get(public_flag, False):
        raise HTTPException(status_code=403, detail=closed_detail)
    check_public_rate_limit(request, scope=scope)


def ensure_public_diagnose_allowed(
    request: Request, wx_user_id: Optional[str] = None
) -> None:
    _ensure_authenticated_or_public(
        request,
        wx_user_id,
        public_flag="allow_public_diagnose",
        scope="diagnose",
        closed_detail="生产环境已关闭公开诊断接口，请登录微信小程序后重试",
    )


def ensure_public_knowledge_search_allowed(request: Request) -> None:
    cfg = _server_cfg()
    if is_production() and not cfg.get("allow_public_knowledge_search", False):
        raise HTTPException(status_code=403, detail="生产环境已关闭公开知识检索")
    check_public_rate_limit(request, scope="knowledge")


def ensure_wx_login_allowed(request: Request) -> None:
    check_public_rate_limit(request, scope="wx_login", default_limit=30)


def ensure_public_vitals_allowed(
    request: Request, wx_user_id: Optional[str] = None
) -> None:
    _ensure_authenticated_or_public(
        request,
        wx_user_id,
        public_flag="allow_public_vitals",
        scope="vitals",
        closed_detail="生产环境已关闭公开生理参数接口，请登录微信小程序后重试",
    )


def ensure_public_pulse_allowed(
    request: Request, wx_user_id: Optional[str] = None
) -> None:
    _ensure_authenticated_or_public(
        request,
        wx_user_id,
        public_flag="allow_public_pulse",
        scope="pulse",
        closed_detail="生产环境已关闭公开脉象分析接口，请登录微信小程序后重试",
    )
