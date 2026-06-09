# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from __future__ import annotations

from typing import Any, Dict, List, Optional

from tcm_ai.domain.pulse.analyzer import PpgWaveformAnalyzer
from tcm_ai.domain.pulse.models import PulseResult
from tcm_ai.domain.pulse.synthetic import synthetic_pulse_waveform

__all__ = ["PulseEngine", "synthetic_pulse_waveform"]


class PulseEngine:
    """脉象分析编排：波形 / 手动 / STM 结果统一入口。"""

    def __init__(self, rules: Optional[Dict[str, Any]] = None) -> None:
        self._analyzer = PpgWaveformAnalyzer(rules)

    @property
    def calibration_version(self) -> str:
        return self._analyzer.calibration_version

    def analyze_from_waveform(
        self,
        samples: List[float],
        fs: float = 100.0,
        imu: Optional[Dict[str, Any]] = None,
        capability_level: str = "L1",
        source: str = "ppg",
    ) -> PulseResult:
        return self._analyzer.analyze_from_waveform(
            samples,
            fs=fs,
            imu=imu,
            capability_level=capability_level,
            source=source,
        )

    def analyze_manual(
        self,
        heart_rate: int,
        pulse: int,
        source: str = "manual",
        capability_level: str = "L0",
    ) -> PulseResult:
        return self._analyzer.analyze_manual(heart_rate, pulse, source, capability_level)

    def analyze_from_stm(self, stm_result: Dict[str, Any]) -> PulseResult:
        waveform = stm_result.get("pulse_waveform") or []
        fs = float(stm_result.get("fs") or 100.0)
        min_samples = fs * 15
        if waveform and len(waveform) >= min_samples:
            result = self.analyze_from_waveform(
                waveform,
                fs=fs,
                imu=stm_result.get("imu"),
                capability_level="L1",
                source="stm",
            )
            if stm_result.get("spo2") is not None:
                result.waveform_stats["spo2"] = stm_result.get("spo2")
            return result

        hr = stm_result.get("heart_rate")
        if hr is not None:
            manual = self.analyze_manual(int(hr), int(hr), source="stm", capability_level="L1")
            if stm_result.get("spo2") is not None:
                manual.waveform_stats["spo2"] = stm_result.get("spo2")
            return manual
        return self._analyzer._failed("no_stm_data", "无有效 STM 脉搏数据", "stm", "L1")

    def enrich_with_knowledge(self, result: PulseResult, tcm_agent: Any) -> PulseResult:
        from tcm_ai.services.pulse_service import PulseDiagnosisTool

        tool = PulseDiagnosisTool(tcm_agent)
        payload = {
            "heart_rate": result.waveform_stats.get("heart_rate", 75),
            "spo2": result.waveform_stats.get("spo2", 98.0),
            "pulse_characteristics": {
                "tcm_interpretation": result.pulse_type,
                "pulse_rate": result.characteristics.rate or "正常",
            },
            "pulse_waveform": result.pulse_waveform,
            "waveform_stats": result.waveform_stats,
            "research_features": result.research_features,
        }
        tool_out = tool.run(payload)
        info = tool_out.get("pulse_info") or {}
        if info.get("description"):
            result.description = info["description"]
        if info.get("interpretation"):
            result.possible_conditions = [info["interpretation"]]
        if info.get("suggestion"):
            result.treatment_recommendations = [info["suggestion"]]
        return result
