import pytest

from tcm_ai.core.security_check import enforce_security_config, validate_security_config


def test_production_blocks_wildcard_cors(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    msgs = validate_security_config(
        {
            "server": {"cors_origins": ["*"], "allow_public_diagnose": False},
            "wechat_miniprogram": {"dev_mode": False, "token_secret": "secret"},
        }
    )
    assert any(m.startswith("ERROR:") and "cors" in m.lower() for m in msgs)


def test_production_blocks_dev_mode(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    msgs = validate_security_config(
        {
            "server": {"cors_origins": ["https://example.com"]},
            "wechat_miniprogram": {"dev_mode": True, "token_secret": "secret"},
        }
    )
    assert any("dev_mode" in m for m in msgs)


def test_production_requires_token_secret(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    msgs = validate_security_config(
        {
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
                "server": {"cors_origins": ["*"]},
                "wechat_miniprogram": {"dev_mode": True, "token_secret": ""},
            }
        )


def test_production_blocks_public_diagnose(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    msgs = validate_security_config(
        {
            "server": {
                "cors_origins": ["https://example.com"],
                "allow_public_diagnose": True,
            },
            "wechat_miniprogram": {"dev_mode": False, "token_secret": "secret"},
        }
    )
    assert any("allow_public_diagnose" in m and m.startswith("ERROR:") for m in msgs)


def test_production_warns_long_wx_token_ttl(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "production")
    msgs = validate_security_config(
        {
            "server": {"cors_origins": ["https://example.com"]},
            "wechat_miniprogram": {
                "dev_mode": False,
                "token_secret": "secret",
                "token_ttl_hours": 720,
            },
        }
    )
    assert any("token_ttl_hours" in m and m.startswith("WARN:") for m in msgs)
