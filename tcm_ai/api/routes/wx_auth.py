from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from tcm_ai.api.public_access import ensure_wx_login_allowed

from tcm_ai.api.wx_user_auth import _extract_bearer, get_optional_wx_user_id, require_wx_user_id
from tcm_ai.services.user_service import WxUserService
from tcm_ai.services.wechat_auth_service import WechatAuthError, WechatAuthService
from tcm_ai.services.wx_token import get_expires_in, issue_token, refresh_access_token, verify_token

router = APIRouter(prefix="/api/wx", tags=["微信小程序"])

_user_service = WxUserService()
_wechat_auth = WechatAuthService()


class WxLoginRequest(BaseModel):
    code: str = Field(..., min_length=1, description="wx.login 返回的 code")


class WxProfileUpdate(BaseModel):
    nickName: Optional[str] = Field(default=None, max_length=64)
    avatarUrl: Optional[str] = Field(default=None, max_length=512)
    cloudHistoryIndexFileId: Optional[str] = Field(default=None, max_length=512)


@router.post("/login")
def wx_login(request: Request, payload: WxLoginRequest) -> Dict[str, Any]:
    ensure_wx_login_allowed(request)
    try:
        session = _wechat_auth.exchange_code(payload.code)
    except WechatAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user = _user_service.upsert_by_openid(
        session["openid"],
        unionid=session.get("unionid") or None,
    )
    issued = issue_token(user["id"])
    return {
        **issued,
        "user": _user_service.public_view(user),
    }


@router.post("/refresh")
def wx_refresh_token(
    authorization: Optional[str] = Header(default=None),
    x_wx_token: Optional[str] = Header(default=None, alias="X-WX-Token"),
) -> Dict[str, Any]:
    token = _extract_bearer(authorization, x_wx_token)
    if not token:
        raise HTTPException(status_code=401, detail="请先登录微信小程序")
    new_token = refresh_access_token(token)
    if not new_token:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    user_id = verify_token(new_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    user = _user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return {
        "token": new_token,
        "expires_in": get_expires_in(),
        "user": _user_service.public_view(user),
    }


@router.get("/me")
def wx_me(user_id: str = Depends(require_wx_user_id)) -> Dict[str, Any]:
    user = _user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"user": _user_service.public_view(user)}


@router.put("/profile")
def wx_update_profile(
    payload: WxProfileUpdate,
    user_id: str = Depends(require_wx_user_id),
) -> Dict[str, Any]:
    user = _user_service.update_profile(
        user_id,
        nick_name=payload.nickName,
        avatar_url=payload.avatarUrl,
        cloud_history_index_file_id=payload.cloudHistoryIndexFileId,
    )
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"ok": True, "user": _user_service.public_view(user)}


@router.get("/session")
def wx_session_probe(
    user_id: Optional[str] = Depends(get_optional_wx_user_id),
) -> Dict[str, Any]:
    if not user_id:
        return {"logged_in": False}
    user = _user_service.get_by_id(user_id)
    if not user:
        return {"logged_in": False}
    return {"logged_in": True, "user": _user_service.public_view(user)}
