from typing import TYPE_CHECKING, Any, Dict, List

from fastapi import APIRouter, Depends, Request

from tcm_ai.api.deps import get_knowledge_service, get_rag_pipeline
from tcm_ai.api.public_access import ensure_public_knowledge_search_allowed
from tcm_ai.api.schemas.admin import KnowledgeSearchRequest

if TYPE_CHECKING:
    from tcm_ai.rag.pipeline import RAGPipeline
    from tcm_ai.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])


def _keyword_fallback(
    knowledge_service: "KnowledgeService", query: str, top_k: int
) -> List[Dict[str, Any]]:
    return knowledge_service.search_keywords(query, top_k)


@router.post("/search")
def public_knowledge_search(
    request: Request,
    payload: KnowledgeSearchRequest,
    rag_pipeline: "RAGPipeline" = Depends(get_rag_pipeline),
    knowledge_service: "KnowledgeService" = Depends(get_knowledge_service),
):
    """公开知识检索（向量检索 + rerank；失败时回退关键词检索）。"""
    ensure_public_knowledge_search_allowed(request)
    try:
        results = rag_pipeline.search_knowledge(
            payload.query, top_k=payload.top_k, source="public"
        )
        if results:
            return {"query": payload.query, "results": results, "mode": "vector"}
    except Exception as exc:
        print(f"向量检索失败: {exc}，回退到关键词检索")

    results = _keyword_fallback(knowledge_service, payload.query, payload.top_k)
    return {"query": payload.query, "results": results, "mode": "keyword"}
