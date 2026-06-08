from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ConfigUpdate(BaseModel):
    admin_api_key: Optional[str] = None
    embedding: Optional[Dict[str, Any]] = None
    llm: Optional[Dict[str, Any]] = None
    rerank: Optional[Dict[str, Any]] = None
    rag: Optional[Dict[str, Any]] = None
    server: Optional[Dict[str, Any]] = None
    rbac: Optional[Dict[str, Any]] = None
    wechat_miniprogram: Optional[Dict[str, Any]] = None


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    retrieval_top_k: Optional[int] = Field(default=None, ge=1, le=100)
    final_top_k: Optional[int] = Field(default=None, ge=1, le=20)
    enable_llm_answer: Optional[bool] = None


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeUploadRequest(BaseModel):
    path: str = Field(..., min_length=1, max_length=500, description="相对 tcm_knowledge/ 的路径")
    content: str = Field(..., min_length=1)
    overwrite: bool = False


class PatientCreate(BaseModel):
    patient_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=100)
    gender: Optional[str] = None
    age: Optional[int] = Field(default=None, ge=0, le=150)
    phone: Optional[str] = None
    id_number: Optional[str] = None
    address: Optional[str] = None
    constitution: Optional[str] = None
    allergies: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "active"


class PatientUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    gender: Optional[str] = None
    age: Optional[int] = Field(default=None, ge=0, le=150)
    phone: Optional[str] = None
    id_number: Optional[str] = None
    address: Optional[str] = None
    constitution: Optional[str] = None
    allergies: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class VisitCreate(BaseModel):
    visit_date: Optional[str] = None
    chief_complaint: Optional[str] = ""
    symptoms: Optional[str] = ""
    diagnosis: Optional[str] = ""
    syndrome: Optional[str] = ""
    treatment: Optional[str] = ""
    efficacy: Optional[str] = ""
    notes: Optional[str] = ""
    source: Optional[str] = "manual"


class ProviderTestRequest(BaseModel):
    """测试未保存的表单配置；空 api_key 则沿用已保存值。"""

    provider: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    top_n: Optional[int] = Field(default=None, ge=1, le=50)
