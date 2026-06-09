# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from unittest.mock import MagicMock

from tcm_ai.domain.pulse.classifier_rules import classify_manual, classify_rate_rhythm
from tcm_ai.services.pulse_engine import PulseEngine, synthetic_pulse_waveform


def test_classify_chi_pulse():
    label = classify_rate_rhythm(55.0, 0.02, valid_beat_count=20)
    assert label.pulse_type == "迟脉"
    assert label.characteristics.rate == "迟"
    assert label.characteristics.depth is None


def test_classify_shu_pulse():
    label = classify_rate_rhythm(95.0, 0.02)
    assert label.pulse_type == "数脉"


def test_classify_manual_pinghe():
    label = classify_manual(75)
    assert label.pulse_type == "平和脉"


def test_analyze_synthetic_waveform_returns_research_features():
    engine = PulseEngine()
    samples = synthetic_pulse_waveform(duration_sec=20.0, fs=100.0, bpm=72.0)
    result = engine.analyze_from_waveform(samples, fs=100.0)
    assert result.success is True
    assert result.research_features.get("systolic_amplitude", 0) > 0
    assert result.research_features.get("rise_time_ms", 0) > 0
    assert result.characteristics.depth is None
    assert result.waveform_stats.get("heart_rate", 0) > 0
    assert "lf_hf_ratio" in result.research_features
    assert result.waveform_stats.get("still_duration_sec", 0) >= 0


def test_analyze_manual_low_confidence():
    engine = PulseEngine()
    result = engine.analyze_manual(75, 75)
    assert result.confidence <= 0.5
    assert result.research_features == {}


def test_analyze_short_waveform_fails():
    engine = PulseEngine()
    result = engine.analyze_from_waveform([1, 2, 3], fs=100.0)
    assert result.success is False


def test_enrich_with_knowledge():
    engine = PulseEngine()
    result = engine.analyze_manual(55, 55)
    enriched = engine.enrich_with_knowledge(result, MagicMock())
    assert enriched.possible_conditions or enriched.description
