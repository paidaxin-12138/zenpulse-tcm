# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import pytest

from tcm_ai.core.json_io import update_json_file
from tcm_ai.services import wechat_auth_service as wx_module
from tcm_ai.services.wechat_auth_service import WechatAuthError, WechatAuthService


def test_update_json_file_atomic(tmp_path):
    path = str(tmp_path / "data.json")
    result = update_json_file(path, [], lambda items: items + [{"id": 1}])
    assert result == [{"id": 1}]
    result = update_json_file(path, [], lambda items: items + [{"id": 2}])
    assert len(result) == 2


def test_wechat_dev_mode_requires_explicit_flag(monkeypatch):
    monkeypatch.setenv("TCM_ENV", "development")
    monkeypatch.setattr(
        wx_module,
        "load_config",
        lambda: {"wechat_miniprogram": {"app_id": "", "app_secret": ""}},
    )
    svc = WechatAuthService()
    assert svc._dev_mode_enabled() is False

    with pytest.raises(WechatAuthError):
        svc.exchange_code("any-code")
