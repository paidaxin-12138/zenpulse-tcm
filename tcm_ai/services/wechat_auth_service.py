# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""微信 jscode2session 与开发模式登录。"""

import hashlib
from typing import Any, Dict

import httpx

from tcm_ai.core.config_store import load_config
from tcm_ai.core.runtime import is_production


class WechatAuthError(Exception):
    def __init__(self, message: str, *, errcode: int = 0):
        super().__init__(message)
        self.errcode = errcode


class WechatAuthService:
    Jscode2SessionUrl = "https://api.weixin.qq.com/sns/jscode2session"

    def _wx_config(self) -> Dict[str, Any]:
        return load_config().get("wechat_miniprogram") or {}

    def _dev_mode_enabled(self) -> bool:
        if is_production():
            return False
        cfg = self._wx_config()
        return cfg.get("dev_mode") is True

    def exchange_code(self, code: str) -> Dict[str, str]:
        code = (code or "").strip()
        if not code:
            raise WechatAuthError("缺少登录 code")

        if self._dev_mode_enabled():
            digest = hashlib.sha256(code.encode("utf-8")).hexdigest()[:16]
            return {
                "openid": f"dev_{digest}",
                "session_key": f"dev_sk_{digest}",
                "unionid": "",
            }

        cfg = self._wx_config()
        app_id = cfg.get("app_id", "").strip()
        app_secret = cfg.get("app_secret", "").strip()
        if not app_id or not app_secret:
            raise WechatAuthError("未配置微信小程序 app_id / app_secret")

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    self.Jscode2SessionUrl,
                    params={
                        "appid": app_id,
                        "secret": app_secret,
                        "js_code": code,
                        "grant_type": "authorization_code",
                    },
                )
                data = resp.json()
        except httpx.HTTPError as exc:
            raise WechatAuthError(f"微信登录请求失败: {exc}") from exc

        if data.get("errcode"):
            raise WechatAuthError(
                data.get("errmsg") or "微信登录失败",
                errcode=int(data.get("errcode") or 0),
            )

        openid = data.get("openid") or ""
        if not openid:
            raise WechatAuthError("微信未返回 openid")

        return {
            "openid": openid,
            "session_key": data.get("session_key") or "",
            "unionid": data.get("unionid") or "",
        }
