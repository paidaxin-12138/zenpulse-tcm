"""进程内 AI / RAG 服务单例（API 与服务层共用，避免 services → api 反向依赖）。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from tcm_ai.rag.pipeline import RAGPipeline
    from tcm_ai.services.diagnosis_service import DiagnosisService
    from tcm_ai.services.knowledge_service import KnowledgeService
    from tcm_ai.services.tcm_agent import TCMAgent

_rag_pipeline: Optional[Any] = None
_tcm_agent: Optional[Any] = None
_diagnosis_service: Optional[Any] = None
_knowledge_service: Optional[Any] = None


def reset_ai_cache() -> None:
    """配置或知识库变更后，丢弃 AI/RAG 相关缓存。"""
    global _rag_pipeline, _tcm_agent, _diagnosis_service, _knowledge_service
    if _rag_pipeline is not None:
        _rag_pipeline.vector_index.invalidate()
    _rag_pipeline = None
    _tcm_agent = None
    _diagnosis_service = None
    _knowledge_service = None


def get_rag_pipeline() -> "RAGPipeline":
    global _rag_pipeline
    if _rag_pipeline is None:
        from tcm_ai.rag.pipeline import RAGPipeline

        _rag_pipeline = RAGPipeline()
    return _rag_pipeline


def get_tcm_agent() -> "TCMAgent":
    global _tcm_agent
    if _tcm_agent is None:
        from tcm_ai.services.tcm_agent import TCMAgent

        _tcm_agent = TCMAgent(rag_pipeline=get_rag_pipeline())
    return _tcm_agent


def get_diagnosis_service() -> "DiagnosisService":
    global _diagnosis_service
    if _diagnosis_service is None:
        from tcm_ai.services.diagnosis_service import DiagnosisService

        _diagnosis_service = DiagnosisService(tcm_agent=get_tcm_agent())
    return _diagnosis_service


def get_knowledge_service() -> "KnowledgeService":
    global _knowledge_service
    if _knowledge_service is None:
        from tcm_ai.services.knowledge_service import KnowledgeService

        _knowledge_service = KnowledgeService()
    return _knowledge_service
