# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from unittest.mock import MagicMock

from tcm_ai.services.pulse_service import PulseDiagnosisTool


def test_waveform_stats_empty():
    tool = PulseDiagnosisTool(MagicMock())
    stats = tool._extract_waveform_stats([])
    assert stats["mean"] == 0.0
    assert stats["amplitude"] == 0.0


def test_waveform_stats_values():
    tool = PulseDiagnosisTool(MagicMock())
    stats = tool._extract_waveform_stats([1.0, 2.0, 3.0])
    assert stats["mean"] == 2.0
    assert stats["amplitude"] == 2.0


def test_diagnosis_suggestion_known_pulse():
    tool = PulseDiagnosisTool(MagicMock())
    info = tool._generate_diagnosis_suggestion("迟脉", [])
    assert "迟" in info["description"]
    assert info["formula"]


def test_diagnosis_suggestion_merges_knowledge_titles():
    tool = PulseDiagnosisTool(MagicMock())
    knowledge = [{"title": "四君子汤方剂"}, {"title": "八珍汤方"}]
    info = tool._generate_diagnosis_suggestion("虚脉", knowledge)
    assert "四君子汤" in info["formula"]
