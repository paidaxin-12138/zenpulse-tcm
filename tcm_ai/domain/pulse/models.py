# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class QualityReport:
    score: float
    valid_beat_ratio: float
    still_duration_sec: float
    motion_rejected_sec: float
    valid_beat_count: int
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PulseCharacteristics:
    rate: Optional[str] = None
    rhythm: Optional[str] = None
    strength: Optional[str] = None
    depth: Optional[str] = None
    shape: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PulseResult:
    success: bool
    pulse_type: str
    description: str
    confidence: float
    source: str
    capability_level: str
    limitations: List[str]
    calibration_version: str
    characteristics: PulseCharacteristics
    waveform_stats: Dict[str, Any]
    research_features: Dict[str, Any]
    pulse_waveform: List[float]
    quality: QualityReport
    possible_conditions: List[str] = field(default_factory=list)
    treatment_recommendations: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "pulse_type": self.pulse_type,
            "description": self.description,
            "confidence": self.confidence,
            "source": self.source,
            "capability_level": self.capability_level,
            "limitations": list(self.limitations),
            "calibration_version": self.calibration_version,
            "characteristics": self.characteristics.to_dict(),
            "waveform_stats": dict(self.waveform_stats),
            "research_features": dict(self.research_features),
            "research_features_note": "仅供后台与标定使用，未映射为形态脉名",
            "pulse_waveform": list(self.pulse_waveform),
            "quality": self.quality.to_dict(),
            "possible_conditions": list(self.possible_conditions),
            "treatment_recommendations": list(self.treatment_recommendations),
            "error": self.error,
        }

    def to_clinical_dict(self) -> Dict[str, Any]:
        """与 DiagnosisService / pulse_characteristics 兼容的精简视图。"""
        data = self.to_dict()
        for key in (
            "success",
            "research_features",
            "research_features_note",
            "calibration_version",
            "error",
        ):
            data.pop(key, None)
        return data
