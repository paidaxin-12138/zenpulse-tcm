"""启动时安全配置校验。"""

from __future__ import annotations

from typing import List

from tcm_ai.core.runtime import is_production, is_development


def validate_security_config(config: dict) -> List[str]:
    """返回警告/错误消息列表；生产环境下含 ERROR 前缀项应阻断启动。"""
    messages: List[str] = []
    server = config.get("server") or {}
    wx = config.get("wechat_miniprogram") or {}

    cors = server.get("cors_origins") or []
    if is_production() and "*" in cors:
        messages.append("ERROR: 生产环境 cors_origins 不可为 '*'")

    if is_production() and wx.get("dev_mode"):
        messages.append("ERROR: 生产环境禁止 wechat_miniprogram.dev_mode=true")

    token_secret = (wx.get("token_secret") or "").strip()
    if is_production() and not token_secret:
        messages.append("ERROR: 生产环境必须配置 wechat_miniprogram.token_secret")

    if is_development() and not token_secret:
        messages.append("WARN: 未配置 token_secret，将使用开发专用密钥（勿用于生产）")

    if is_production() and server.get("allow_public_diagnose"):
        messages.append("ERROR: 生产环境禁止 allow_public_diagnose=true")

    if is_production() and server.get("allow_public_knowledge_search"):
        messages.append("ERROR: 生产环境禁止 allow_public_knowledge_search=true")

    try:
        wx_ttl = int(wx.get("token_ttl_hours", 72))
    except (TypeError, ValueError):
        wx_ttl = 72
    if is_production() and wx_ttl > 168:
        messages.append("WARN: wechat_miniprogram.token_ttl_hours 建议 <= 168（推荐 24–72）")

    return messages


def enforce_security_config(config: dict) -> None:
    messages = validate_security_config(config)
    errors = [m for m in messages if m.startswith("ERROR:")]
    for msg in messages:
        print(("⚠ " if msg.startswith("WARN:") else "✗ ") + msg.replace("ERROR: ", "").replace("WARN: ", ""))
    if errors and is_production():
        raise RuntimeError("安全配置校验失败: " + errors[0].replace("ERROR: ", ""))
