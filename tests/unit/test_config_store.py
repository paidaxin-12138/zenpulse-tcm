# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from tcm_ai.core.config_store import MASK, load_config, mask_config, merge_config_update


def test_mask_config_hides_secrets():
    cfg = load_config()
    masked = mask_config(cfg)
    if cfg.get("admin_api_key"):
        assert masked["admin_api_key"] == MASK
    assert masked.get("admin_api_key_set") is True


def test_merge_config_keeps_secrets_when_masked():
    cfg = load_config()
    update = {"llm": {"api_key": MASK, "model": "test-model"}}
    merged = merge_config_update(cfg, update)
    assert merged["llm"]["model"] == "test-model"
    if cfg["llm"].get("api_key"):
        assert merged["llm"]["api_key"] == cfg["llm"]["api_key"]
