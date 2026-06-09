# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from typing import List, Optional

from pydantic import BaseModel, Field

from tcm_ai.domain.vitals.constants import VITALS_MAX_SAMPLES


class VitalsAnalyzeRequest(BaseModel):
    samples: List[float] = Field(..., min_length=1, max_length=VITALS_MAX_SAMPLES, description="MAX30102 CH1 IR 序列")
    samples_ch2: Optional[List[float]] = Field(
        default=None, max_length=VITALS_MAX_SAMPLES, description="CH2 IR 序列（可选）"
    )
    fs: float = Field(default=100.0, gt=0)
    source: str = Field(default="max30102_ble", max_length=64)


class VitalsAnalyzeResponse(BaseModel):
    success: bool
    heart_rate: float = 0.0
    pulse: int = 0
    spo2: float = 0.0
    hr_status: str = ""
    spo2_status: str = ""
    overall_status: str = ""
    alerts: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    quality_score: float = 0.0
    source: str = ""
    sample_count: int = 0
    duration_sec: float = 0.0
    limitations: List[str] = Field(default_factory=list)
    disclaimer: str = ""
    error: Optional[str] = None
