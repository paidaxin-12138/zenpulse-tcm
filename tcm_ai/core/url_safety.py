# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""出站 URL 校验，降低 Editor 测模型接口的 SSRF 风险。"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from tcm_ai.core.runtime import is_development


class UnsafeUrlError(ValueError):
    pass


def _is_blocked_ip(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return bool(
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    )


def validate_outbound_base_url(url: str, *, field_name: str = "base_url") -> str:
    """校验 HTTP(S) base_url；生产环境禁止指向内网/本机（Ollama 请用配置文件固定地址）。"""
    raw = (url or "").strip()
    if not raw:
        raise UnsafeUrlError(f"{field_name} 不能为空")

    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeUrlError(f"{field_name} 仅支持 http/https")
    if parsed.username or parsed.password:
        raise UnsafeUrlError(f"{field_name} 不可包含用户名或密码")

    host = (parsed.hostname or "").strip().lower()
    if not host:
        raise UnsafeUrlError(f"{field_name} 缺少主机名")

    if is_development():
        return raw.rstrip("/")

    if host in ("localhost", "metadata.google.internal"):
        raise UnsafeUrlError(f"{field_name} 在生产环境不可指向 {host}")

    try:
        addr = ipaddress.ip_address(host)
        if _is_blocked_ip(addr):
            raise UnsafeUrlError(f"{field_name} 在生产环境不可指向内网或保留地址")
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, None)
        except socket.gaierror as exc:
            raise UnsafeUrlError(f"{field_name} 无法解析主机: {host}") from exc
        for info in infos:
            ip_str = info[4][0]
            try:
                addr = ipaddress.ip_address(ip_str)
            except ValueError:
                continue
            if _is_blocked_ip(addr):
                raise UnsafeUrlError(f"{field_name} 在生产环境不可解析到内网地址")

    return raw.rstrip("/")
