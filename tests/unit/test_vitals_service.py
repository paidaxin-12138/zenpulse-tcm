# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from tcm_ai.domain.pulse.synthetic import synthetic_pulse_waveform
from tcm_ai.services.vitals_service import VitalsService


def test_analyze_synthetic_samples():
    service = VitalsService()
    samples = synthetic_pulse_waveform(duration_sec=10.0, fs=100.0, bpm=72.0)
    result = service.analyze_samples(samples, fs=100.0, source="test")
    assert result.success is True
    assert 55 <= result.heart_rate <= 95
    assert result.spo2 > 0
    assert result.hr_status in {"正常", "偏慢", "偏快"}


def test_analyze_manual_bradycardia():
    service = VitalsService()
    result = service.analyze_manual(55, 55, spo2=98.0)
    assert result.hr_status == "偏慢"
    assert result.overall_status in {"需关注", "正常", "待确认"}


def test_analyze_manual_unknown_spo2_when_omitted():
    service = VitalsService()
    result = service.analyze_manual(80, 80)
    assert result.spo2 == 0.0
    assert result.spo2_status == "未知"


def test_rejects_short_sample():
    service = VitalsService()
    result = service.analyze_samples([1, 2, 3], fs=100.0)
    assert result.success is False


def test_rejects_when_merged_channel_length_below_minimum():
    """CH1 够长但 CH2 截断导致有效点数不足时应失败。"""
    service = VitalsService()
    samples = synthetic_pulse_waveform(duration_sec=10.0, fs=100.0, bpm=72.0)
    ch2 = samples[:400]
    result = service.analyze_samples(
        samples,
        fs=100.0,
        samples_ch2=ch2,
        source="max30102_ble",
    )
    assert result.success is False
    assert "采样不足" in (result.error or "")


def test_analyze_samples_warns_on_channel_length_mismatch():
    service = VitalsService()
    samples = synthetic_pulse_waveform(duration_sec=10.0, fs=100.0, bpm=72.0)
    ch2 = samples[: len(samples) - 50]
    result = service.analyze_samples(
        samples,
        fs=100.0,
        samples_ch2=ch2,
        source="max30102_ble",
    )
    assert result.success is True
    assert any("双通道采样点数不一致" in alert for alert in result.alerts)
    assert result.quality_score < 1.0
