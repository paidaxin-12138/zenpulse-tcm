from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from tcm_ai.core.request_limits import MAX_DIAGNOSE_IMAGE_B64_CHARS
from tcm_ai.domain.vitals.constants import VITALS_MAX_SAMPLES


class DiagnoseImages(BaseModel):
    tongue: Optional[str] = Field(default=None, description="舌苔 base64")
    face: Optional[str] = Field(default=None, description="面部 base64")
    eye: Optional[str] = Field(default=None, description="眼部 base64")

    @field_validator("tongue", "face", "eye")
    @classmethod
    def validate_image_b64_size(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and len(value) > MAX_DIAGNOSE_IMAGE_B64_CHARS:
            raise ValueError(
                f"图片 base64 超过上限（最大 {MAX_DIAGNOSE_IMAGE_B64_CHARS} 字符）"
            )
        return value


class DiagnoseJsonRequest(BaseModel):
    heart_rate: int = Field(..., ge=30, le=220)
    pulse: int = Field(..., ge=30, le=220)
    systolic: int = Field(..., ge=60, le=250)
    diastolic: int = Field(..., ge=40, le=150)
    age: Optional[int] = Field(default=None, ge=0, le=150)
    gender: Optional[str] = None
    images: Optional[DiagnoseImages] = None
    pulse_waveform: Optional[List[float]] = Field(
        default=None,
        max_length=VITALS_MAX_SAMPLES,
        description="MAX30102 CH1 原始序列",
    )
    max30102_samples_ch2: Optional[List[float]] = Field(
        default=None,
        max_length=VITALS_MAX_SAMPLES,
        description="MAX30102 CH2 原始序列（可选）",
    )
    pulse_fs: Optional[float] = Field(default=100.0, gt=0)
    pulse_source: Optional[str] = Field(default="manual", max_length=64)
    spo2: Optional[float] = Field(default=None, ge=0, le=100)
    vitals_assessment: Optional[Dict[str, Any]] = Field(
        default=None,
        description="体征页 /vitals/analyze 已分析结果，优先透传",
    )


class DiagnoseResponse(BaseModel):
    diagnosis: str = Field(..., description="完整诊断报告（Markdown/文本，兼容旧客户端）")
    source: str
    vitals_assessment: dict = Field(default_factory=dict, description="MAX30102 生理参数评估")
    pulse_characteristics: dict = Field(default_factory=dict, description="已弃用，保留空对象兼容旧客户端")
    disclaimer: str
    syndrome: str = Field(default="", description="中医辨证/证型")
    analysis: str = Field(default="", description="证候分析")
    suggestions: List[str] = Field(default_factory=list, description="调理与生活建议")
    prescriptions: List[str] = Field(default_factory=list, description="中药/方剂建议")
    face_analysis: List[str] = Field(default_factory=list)
    tongue_analysis: List[str] = Field(default_factory=list)
    eye_analysis: List[str] = Field(default_factory=list)
    fusion_summary: Optional[str] = Field(default=None, description="多模态融合摘要")
    diagnosis_mode: Optional[str] = Field(default=None, description="llm | rule | metrics")
    llm_fallback_reason: Optional[str] = Field(default=None, description="规则降级原因")
