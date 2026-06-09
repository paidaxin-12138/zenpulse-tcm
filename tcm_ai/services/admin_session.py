# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""管理端 HttpOnly Cookie 会话（HMAC 签名；登出可 Redis 黑名单撤销）。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from threading import Lock
from typing import Any, Dict, Optional

from tcm_ai.core.config_store import load_config
from tcm_ai.core.redis_client import get_redis
from tcm_ai.core.runtime import is_production

COOKIE_NAME = "tcm_admin_session"
_runtime_dev_secret: Optional[str] = None
_revoked_lock = Lock()
_revoked_local: Dict[str, float] = {}


def _get_dev_runtime_secret() -> str:
    global _runtime_dev_secret
    if _runtime_dev_secret is None:
        _runtime_dev_secret = secrets.token_hex(32)
    return _runtime_dev_secret


def _get_secret() -> str:
    config = load_config()
    server = config.get("server") or {}
    secret = (server.get("admin_session_secret") or "").strip()
    if secret:
        return secret
    wx = config.get("wechat_miniprogram") or {}
    secret = (wx.get("token_secret") or "").strip()
    if secret:
        return secret
    if is_production():
        raise RuntimeError("生产环境必须配置 server.admin_session_secret 或 wechat_miniprogram.token_secret")
    return _get_dev_runtime_secret()


def _get_ttl_seconds() -> int:
    config = load_config()
    hours = (config.get("server") or {}).get("admin_session_ttl_hours", 8)
    try:
        hours = int(hours)
    except (TypeError, ValueError):
        hours = 8
    return max(1, hours) * 3600


def _parse_payload(token: str, *, check_expiry: bool = True) -> Optional[Dict[str, Any]]:
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
    if payload.get("typ") != "admin_session":
        return None
    exp = payload.get("exp")
    role = payload.get("role")
    if not role or not isinstance(exp, (int, float)):
        return None
    if check_expiry and exp < time.time():
        return None
    return payload


def _is_revoked(jti: Optional[str]) -> bool:
    if not jti:
        return False
    client = get_redis()
    if client:
        try:
            return bool(client.get(f"tcm:admin:revoked:{jti}"))
        except Exception:
            pass
    now = time.time()
    with _revoked_lock:
        exp = _revoked_local.get(jti)
        if exp is None:
            return False
        if exp <= now:
            _revoked_local.pop(jti, None)
            return False
        return True


def revoke_session_token(token: Optional[str]) -> None:
    payload = _parse_payload(token or "", check_expiry=False)
    if not payload:
        return
    jti = payload.get("jti")
    if not jti:
        return
    ttl = max(1, int(payload.get("exp", 0) - time.time()))
    client = get_redis()
    if client:
        try:
            client.setex(f"tcm:admin:revoked:{jti}", ttl, "1")
            return
        except Exception:
            pass
    with _revoked_lock:
        _revoked_local[str(jti)] = time.time() + ttl


def reset_revoked_sessions_for_tests() -> None:
    with _revoked_lock:
        _revoked_local.clear()


def create_session_token(role: str, display_name: str = "") -> str:
    payload = {
        "typ": "admin_session",
        "role": role,
        "name": (display_name or "")[:64],
        "exp": int(time.time()) + _get_ttl_seconds(),
        "jti": secrets.token_hex(8),
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    data = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    sig = hmac.new(_get_secret().encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{data}.{sig}"


def verify_session_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    payload = _parse_payload(token or "", check_expiry=True)
    if not payload:
        return None
    if _is_revoked(payload.get("jti")):
        return None
    return {
        "role": str(payload["role"]),
        "display_name": str(payload.get("name") or ""),
        "jti": str(payload.get("jti") or ""),
    }
