from typing import List, Optional

from pydantic import BaseModel, Field


class DiagnoseImages(BaseModel):
    tongue: Optional[str] = Field(default=None, description="舌苔 base64")
    face: Optional[str] = Field(default=None, description="面部 base64")
    eye: Optional[str] = Field(default=None, description="眼部 base64")


class DiagnoseJsonRequest(BaseModel):
    heart_rate: int = Field(..., ge=30, le=220)
    pulse: int = Field(..., ge=30, le=220)
    systolic: int = Field(..., ge=60, le=250)
    diastolic: int = Field(..., ge=40, le=150)
    age: Optional[int] = Field(default=None, ge=0, le=150)
    gender: Optional[str] = None
    images: Optional[DiagnoseImages] = None


class DiagnoseResponse(BaseModel):
    diagnosis: str = Field(..., description="完整诊断报告（Markdown/文本，兼容旧客户端）")
    source: str
    pulse_characteristics: dict
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
