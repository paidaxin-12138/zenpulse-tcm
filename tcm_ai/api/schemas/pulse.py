# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from tcm_ai.domain.vitals.constants import VITALS_MAX_SAMPLES


class PulseImu(BaseModel):
    acc_x: Optional[List[float]] = Field(default=None, max_length=VITALS_MAX_SAMPLES)
    acc_y: Optional[List[float]] = Field(default=None, max_length=VITALS_MAX_SAMPLES)
    acc_z: Optional[List[float]] = Field(default=None, max_length=VITALS_MAX_SAMPLES)
    fs: float = Field(default=50.0, gt=0)


class PulseAnalyzeRequest(BaseModel):
    samples: List[float] = Field(..., min_length=1, max_length=VITALS_MAX_SAMPLES)
    fs: float = Field(default=100.0, gt=0)
    source: str = Field(default="ppg", max_length=64)
    capability_level: str = Field(default="L1")
    imu: Optional[PulseImu] = None
    metadata: Optional[Dict[str, Any]] = None


class PulseAnalyzeResponse(BaseModel):
    success: bool
    pulse_type: str = ""
    description: str = ""
    confidence: float = 0.0
    source: str = ""
    capability_level: str = "L1"
    limitations: List[str] = Field(default_factory=list)
    calibration_version: str = ""
    characteristics: Dict[str, Any] = Field(default_factory=dict)
    waveform_stats: Dict[str, Any] = Field(default_factory=dict)
    research_features: Dict[str, Any] = Field(default_factory=dict)
    research_features_note: str = ""
    pulse_waveform: List[float] = Field(default_factory=list)
    quality: Dict[str, Any] = Field(default_factory=dict)
    possible_conditions: List[str] = Field(default_factory=list)
    treatment_recommendations: List[str] = Field(default_factory=list)
    disclaimer: str = ""
    error: Optional[str] = None
