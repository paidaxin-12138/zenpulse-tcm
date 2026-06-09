# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import base64
import hashlib
import hmac
import json
import time

import pytest

from tcm_ai.core.request_metrics import (
    format_prometheus_counters,
    normalize_path,
    record_request,
    reset_counters_for_tests,
)
from tcm_ai.services import admin_session
from tcm_ai.services import wx_token as wx_token_module


def test_normalize_path_replaces_ids():
    assert normalize_path("/api/admin/patients/42") == "/api/admin/patients/{id}"
    assert (
        normalize_path("/api/diagnosis/history/550e8400-e29b-41d4-a716-446655440000")
        == "/api/diagnosis/history/{id}"
    )


def test_record_and_export_counters():
    reset_counters_for_tests()
    record_request("GET", "/api/health", 200)
    record_request("GET", "/api/health", 200)
    record_request("POST", "/api/wx/login", 401)
    record_request("GET", "/metrics", 200)

    lines = list(format_prometheus_counters())
    body = "\n".join(lines)
    assert "tcm_http_requests_total" in body
    assert 'route="/api/health"' in body
    assert 'status="200"' in body
    assert body.count('route="/api/health"') >= 1
    assert "/metrics" not in body


def test_wx_refresh_valid_token(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "development")
    token = wx_token_module.create_token("user-1")
    new_token = wx_token_module.refresh_access_token(token)
    assert new_token
    assert wx_token_module.verify_token(new_token) == "user-1"


def _signed_wx_token(user_id: str, exp: int) -> str:
    payload = {"sub": user_id, "exp": exp, "jti": "test-jti"}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    data = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    secret = wx_token_module._get_secret()
    sig = hmac.new(secret.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{data}.{sig}"


def test_wx_refresh_expired_within_grace(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "development")
    monkeypatch.setattr(wx_token_module, "_get_refresh_grace_seconds", lambda: 3600)
    expired = _signed_wx_token("user-2", int(time.time()) - 120)
    assert wx_token_module.refresh_access_token(expired)


def test_wx_refresh_expired_beyond_grace(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "development")
    monkeypatch.setattr(wx_token_module, "_get_refresh_grace_seconds", lambda: 60)
    expired = _signed_wx_token("user-3", int(time.time()) - 3600)
    assert wx_token_module.refresh_access_token(expired) is None


def test_admin_session_revoked_after_logout(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "development")
    monkeypatch.setattr(
        admin_session,
        "load_config",
        lambda: {"server": {}, "wechat_miniprogram": {"token_secret": "test-secret"}},
    )
    admin_session.reset_revoked_sessions_for_tests()
    token = admin_session.create_session_token("admin", "Ops")
    assert admin_session.verify_session_token(token)
    admin_session.revoke_session_token(token)
    assert admin_session.verify_session_token(token) is None
