"""管理端 Cookie 会话登录/登出。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from tcm_ai.api.admin_auth import resolve_admin_role
from tcm_ai.core.rate_limit import (
    check_admin_auth_rate_limit,
    clear_admin_auth_rate_limit,
)
from tcm_ai.core.runtime import is_production
from tcm_ai.services.admin_session import (
    COOKIE_NAME,
    create_session_token,
    revoke_session_token,
    verify_session_token,
    _get_ttl_seconds,
)

router = APIRouter(prefix="/api/admin/session", tags=["管理端"])


class AdminLoginBody(BaseModel):
    api_key: str = Field(min_length=1)
    display_name: str = ""


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_production(),
        samesite="lax",
        max_age=_get_ttl_seconds(),
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")


@router.post("/login")
def admin_session_login(body: AdminLoginBody, request: Request, response: Response) -> dict:
    role = resolve_admin_role(body.api_key)
    if not role:
        check_admin_auth_rate_limit(request)
        raise HTTPException(status_code=401, detail="无效的管理端 API Key")
    clear_admin_auth_rate_limit(request)
    token = create_session_token(role, body.display_name.strip())
    _set_session_cookie(response, token)
    return {"role": role, "display_name": body.display_name.strip()}


@router.post("/logout")
def admin_session_logout(request: Request, response: Response) -> dict:
    revoke_session_token(request.cookies.get(COOKIE_NAME))
    _clear_session_cookie(response)
    return {"ok": True}


@router.get("/me")
def admin_session_me(request: Request) -> dict:
    session = verify_session_token(request.cookies.get(COOKIE_NAME))
    if not session:
        raise HTTPException(status_code=401, detail="未登录或会话已过期")
    return session
