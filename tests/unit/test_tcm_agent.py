# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import logging
from unittest.mock import MagicMock

import pytest

from tcm_ai.services.tcm_agent import TCMAgent


def test_get_tcm_diagnosis_falls_back_to_rule_and_logs_when_llm_fails(
    monkeypatch, caplog
):
    caplog.set_level(logging.WARNING)

    agent = TCMAgent.__new__(TCMAgent)
    agent.model = "test-model"
    agent.rag_pipeline = MagicMock()
    agent.rag_pipeline.search_knowledge.return_value = []
    agent.fusion_engine = None
    agent.rule_engine = None
    agent.knowledge_manager = None
    agent._knowledge_loaded = False

    def _search(_query, top_k=5):
        return []

    monkeypatch.setattr(agent, "_search_related_knowledge", _search)
    monkeypatch.setattr(
        "tcm_ai.services.tcm_agent.invoke_llm",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("LLM down")),
    )

    vision_data = {
        "face": {"skin_color": {"hue": 10, "saturation": 0.3, "value": 0.8}},
        "tongue": {"color": {"hsv": [15, 0.2, 0.7]}, "coating": {"coating_ratio": 0.2}},
        "eyes": [{"bloodshot": {"red_ratio": 0.1, "severity": "轻度"}}],
    }
    stm_data = {"heart_rate": 75, "systolic_pressure": 120, "diastolic_pressure": 80}

    result = agent.get_tcm_diagnosis(vision_data, stm_data)

    assert result["diagnosis_mode"] == "rule"
    assert "LLM down" in result["llm_fallback_reason"]
    assert any("LLM" in rec.message for rec in caplog.records)


def test_search_related_knowledge_logs_vector_failure(monkeypatch, caplog):
    caplog.set_level(logging.WARNING)

    agent = TCMAgent.__new__(TCMAgent)
    agent.rag_pipeline = MagicMock()
    agent.rag_pipeline.search_knowledge.side_effect = RuntimeError("index missing")
    agent.knowledge_manager = MagicMock()
    agent.knowledge_manager.search_knowledge.return_value = [{"title": "fallback"}]
    agent._knowledge_loaded = True

    results = agent._search_related_knowledge("气血不足")

    assert len(results) == 1
    assert any("向量搜索失败" in rec.message for rec in caplog.records)
