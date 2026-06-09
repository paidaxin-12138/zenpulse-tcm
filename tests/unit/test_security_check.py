# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import pytest

from tcm_ai.core.security_check import enforce_security_config, validate_security_config

_GOOD_SECRET = "a" * 32
_GOOD_ADMIN = "b" * 32


def test_production_blocks_wildcard_cors(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    msgs = validate_security_config(
        {
            "admin_api_key": _GOOD_ADMIN,
            "server": {"cors_origins": ["*"], "allow_public_diagnose": False},
            "wechat_miniprogram": {"dev_mode": False, "token_secret": _GOOD_SECRET},
        }
    )
    assert any(m.startswith("ERROR:") and "cors" in m.lower() for m in msgs)


def test_production_blocks_dev_mode(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    msgs = validate_security_config(
        {
            "admin_api_key": _GOOD_ADMIN,
            "server": {"cors_origins": ["https://example.com"]},
            "wechat_miniprogram": {"dev_mode": True, "token_secret": _GOOD_SECRET},
        }
    )
    assert any("dev_mode" in m for m in msgs)


def test_production_requires_token_secret(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    msgs = validate_security_config(
        {
            "admin_api_key": _GOOD_ADMIN,
            "server": {"cors_origins": ["https://example.com"]},
            "wechat_miniprogram": {"dev_mode": False, "token_secret": ""},
        }
    )
    assert any("token_secret" in m for m in msgs)


def test_development_warns_missing_token_secret(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "development")
    msgs = validate_security_config(
        {"server": {}, "wechat_miniprogram": {"token_secret": ""}}
    )
    assert any(m.startswith("WARN:") for m in msgs)


def test_enforce_security_config_raises_in_production(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    with pytest.raises(RuntimeError, match="安全配置"):
        enforce_security_config(
            {
                "admin_api_key": _GOOD_ADMIN,
                "server": {"cors_origins": ["*"]},
                "wechat_miniprogram": {"dev_mode": True, "token_secret": ""},
            }
        )


def test_production_blocks_public_diagnose(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    msgs = validate_security_config(
        {
            "admin_api_key": _GOOD_ADMIN,
            "server": {
                "cors_origins": ["https://example.com"],
                "allow_public_diagnose": True,
            },
            "wechat_miniprogram": {"dev_mode": False, "token_secret": _GOOD_SECRET},
        }
    )
    assert any("allow_public_diagnose" in m and m.startswith("ERROR:") for m in msgs)


def test_production_warns_long_wx_token_ttl(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    msgs = validate_security_config(
        {
            "admin_api_key": _GOOD_ADMIN,
            "server": {"cors_origins": ["https://example.com"]},
            "wechat_miniprogram": {
                "dev_mode": False,
                "token_secret": _GOOD_SECRET,
                "token_ttl_hours": 720,
            },
        }
    )
    assert any("token_ttl_hours" in m and m.startswith("WARN:") for m in msgs)


def test_production_rejects_placeholder_token_secret(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    msgs = validate_security_config(
        {
            "admin_api_key": "a" * 32,
            "server": {"cors_origins": ["https://example.com"]},
            "wechat_miniprogram": {
                "dev_mode": False,
                "token_secret": "请用 secrets.token_urlsafe(32) 生成独立密钥",
            },
        }
    )
    assert any("token_secret" in m and m.startswith("ERROR:") for m in msgs)


def test_production_rejects_short_admin_key(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    msgs = validate_security_config(
        {
            "admin_api_key": "too-short",
            "server": {"cors_origins": ["https://example.com"]},
            "wechat_miniprogram": {
                "dev_mode": False,
                "token_secret": "x" * 32,
            },
        }
    )
    assert any("admin_api_key" in m and m.startswith("ERROR:") for m in msgs)


def test_production_blocks_public_vitals(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    msgs = validate_security_config(
        {
            "admin_api_key": _GOOD_ADMIN,
            "server": {
                "cors_origins": ["https://example.com"],
                "allow_public_vitals": True,
            },
            "wechat_miniprogram": {"dev_mode": False, "token_secret": _GOOD_SECRET},
        }
    )
    assert any("allow_public_vitals" in m and m.startswith("ERROR:") for m in msgs)


def test_production_blocks_public_pulse(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    msgs = validate_security_config(
        {
            "admin_api_key": _GOOD_ADMIN,
            "server": {
                "cors_origins": ["https://example.com"],
                "allow_public_pulse": True,
            },
            "wechat_miniprogram": {"dev_mode": False, "token_secret": _GOOD_SECRET},
        }
    )
    assert any("allow_public_pulse" in m and m.startswith("ERROR:") for m in msgs)


def test_is_weak_secret():
    from tcm_ai.core.security_check import is_weak_secret

    assert is_weak_secret("")
    assert is_weak_secret("short")
    assert is_weak_secret("请用 secrets.token_urlsafe(32) 生成")
    assert not is_weak_secret("a" * 32)
