# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""微信小程序 Bearer Token（HMAC 签名，无第三方 JWT 依赖）。"""

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Dict, Optional

from tcm_ai.core.config_store import load_config
from tcm_ai.core.runtime import is_production

_runtime_dev_secret: Optional[str] = None


def _get_dev_runtime_secret() -> str:
    """开发环境未配置 token_secret 时，使用进程内随机密钥（非固定值，重启后 Token 失效）。"""
    global _runtime_dev_secret
    if _runtime_dev_secret is None:
        _runtime_dev_secret = secrets.token_hex(32)
        print("⚠ 开发环境未配置 token_secret，已生成进程内随机密钥（重启后需重新登录）")
    return _runtime_dev_secret


def _get_secret() -> str:
    config = load_config()
    wx_cfg = config.get("wechat_miniprogram") or {}
    secret = (wx_cfg.get("token_secret") or "").strip()
    if secret:
        return secret
    if is_production():
        raise RuntimeError("生产环境必须配置 wechat_miniprogram.token_secret")
    return _get_dev_runtime_secret()


def _get_ttl_seconds() -> int:
    config = load_config()
    wx_cfg = config.get("wechat_miniprogram") or {}
    hours = wx_cfg.get("token_ttl_hours", 72)
    try:
        hours = int(hours)
    except (TypeError, ValueError):
        hours = 72
    return max(1, hours) * 3600


def _get_refresh_grace_seconds() -> int:
    config = load_config()
    wx_cfg = config.get("wechat_miniprogram") or {}
    hours = wx_cfg.get("token_refresh_grace_hours", 168)
    try:
        hours = int(hours)
    except (TypeError, ValueError):
        hours = 168
    return max(0, hours) * 3600


def decode_token_payload(token: Optional[str], *, allow_expired: bool = False) -> Optional[Dict[str, Any]]:
    if not token or "." not in token:
        return None
    data, sig = token.rsplit(".", 1)
    expected = hmac.new(_get_secret().encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    pad = "=" * (-len(data) % 4)
    try:
        payload: Dict[str, Any] = json.loads(base64.urlsafe_b64decode(data + pad))
    except (json.JSONDecodeError, ValueError):
        return None
    sub = payload.get("sub")
    exp = payload.get("exp")
    if not sub or not isinstance(exp, (int, float)):
        return None
    if not allow_expired and exp < time.time():
        return None
    return payload


def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": int(time.time()) + _get_ttl_seconds(),
        "jti": secrets.token_hex(8),
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    data = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    sig = hmac.new(_get_secret().encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{data}.{sig}"


def get_expires_in() -> int:
    return _get_ttl_seconds()


def issue_token(user_id: str) -> Dict[str, Any]:
    return {"token": create_token(user_id), "expires_in": get_expires_in()}


def verify_token(token: Optional[str]) -> Optional[str]:
    payload = decode_token_payload(token, allow_expired=False)
    if not payload:
        return None
    return str(payload["sub"])


def refresh_access_token(token: Optional[str]) -> Optional[str]:
    payload = decode_token_payload(token, allow_expired=True)
    if not payload:
        return None
    exp = float(payload["exp"])
    now = time.time()
    if exp >= now:
        return create_token(str(payload["sub"]))
    if now - exp <= _get_refresh_grace_seconds():
        return create_token(str(payload["sub"]))
    return None
