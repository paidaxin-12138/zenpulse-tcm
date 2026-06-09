# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""微信小程序用户鉴权依赖。"""

from typing import Optional

from fastapi import Header, HTTPException

from tcm_ai.services.user_service import WxUserService
from tcm_ai.services.wx_token import verify_token

_user_service = WxUserService()


def _extract_bearer(authorization: Optional[str], x_wx_token: Optional[str]) -> Optional[str]:
    token = (x_wx_token or "").strip()
    if token:
        return token
    if authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "bearer" and value.strip():
            return value.strip()
    return None


def get_optional_wx_user_id(
    authorization: Optional[str] = Header(default=None),
    x_wx_token: Optional[str] = Header(default=None, alias="X-WX-Token"),
) -> Optional[str]:
    token = _extract_bearer(authorization, x_wx_token)
    if not token:
        return None
    user_id = verify_token(token)
    if not user_id or not _user_service.get_by_id(user_id):
        return None
    return user_id


def require_wx_user_id(
    authorization: Optional[str] = Header(default=None),
    x_wx_token: Optional[str] = Header(default=None, alias="X-WX-Token"),
) -> str:
    user_id = get_optional_wx_user_id(authorization, x_wx_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="请先登录微信小程序")
    return user_id
