# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""管理端 API Key 校验与 RBAC。"""

from enum import IntEnum
from typing import Optional

import secrets
from fastapi import Header, HTTPException, Request

from tcm_ai.core.config_store import load_config
from tcm_ai.core.rate_limit import (
    check_admin_auth_rate_limit,
    clear_admin_auth_rate_limit,
)
from tcm_ai.services.admin_session import COOKIE_NAME, verify_session_token

ROLE_ORDER = {"viewer": 1, "editor": 2, "admin": 3}


class AdminRole(IntEnum):
    VIEWER = 1
    EDITOR = 2
    ADMIN = 3


def resolve_admin_role(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    config = load_config()
    main_key = config.get("admin_api_key", "")
    if main_key and secrets.compare_digest(token, main_key):
        return "admin"
    rbac = config.get("rbac") or {}
    if not rbac.get("enabled"):
        return None
    for entry in rbac.get("keys") or []:
        key = entry.get("key") or ""
        if key and secrets.compare_digest(token, key):
            return entry.get("role") or "viewer"
    return None


def resolve_admin_from_request(
    request: Request,
    header_token: Optional[str],
) -> Optional[str]:
    session = verify_session_token(request.cookies.get(COOKIE_NAME))
    if session:
        return session["role"]
    return resolve_admin_role(header_token)


def verify_admin_api_key(provided: Optional[str]) -> bool:
    return resolve_admin_role(provided) is not None


def _role_level(role: str) -> int:
    return ROLE_ORDER.get(role, 0)


def require_admin_role(min_role: str = "viewer"):
    min_level = _role_level(min_role)

    def _dependency(
        request: Request,
        x_admin_api_key: Optional[str] = Header(default=None, alias="X-Admin-API-Key"),
        authorization: Optional[str] = Header(default=None),
    ) -> str:
        token = x_admin_api_key
        if not token and authorization:
            scheme, _, value = authorization.partition(" ")
            if scheme.lower() == "bearer" and value:
                token = value
        role = resolve_admin_from_request(request, token)
        if not role:
            if token:
                check_admin_auth_rate_limit(request)
            raise HTTPException(status_code=401, detail="无效的管理端 API Key")
        clear_admin_auth_rate_limit(request)
        if _role_level(role) < min_level:
            raise HTTPException(status_code=403, detail=f"需要 {min_role} 及以上权限")
        return role

    return _dependency
