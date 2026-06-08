from typing import Any, Dict, List, Optional

from tcm_ai.core.config_store import load_config
from tcm_ai.services.rag_log_service import log_rag_event


class RAGPipeline:
    def __init__(self) -> None:
        from tcm_ai.rag.vector_index import VectorIndexService

        self.vector_index = VectorIndexService()

    def search_knowledge(
        self, query: str, top_k: int = 5, source: str = "diagnosis"
    ) -> List[Dict[str, Any]]:
        """检索知识片段（向量 + rerank），供诊断端复用，不调用 LLM。"""
        import time

        from tcm_ai.rag.providers import rerank_documents

        started = time.perf_counter()
        config = load_config()
        rag_cfg = config["rag"]
        retrieval_k = max(int(rag_cfg.get("retrieval_top_k", 20)), top_k)
        final_k = top_k
        rerank_top_n = int(config["rerank"].get("top_n", final_k))

        retrieved = self.vector_index.search(query, top_k=retrieval_k)
        reranked = rerank_documents(
            config["rerank"], query, retrieved, top_n=max(final_k, rerank_top_n)
        )
        for item in reranked:
            if "rerank_score" not in item:
                item["rerank_score"] = item.get("score", 0.0)
        results = reranked[:final_k]

        log_rag_event(
            "search",
            query,
            retrieved_count=len(retrieved),
            final_top_k=final_k,
            providers={
                "embedding": config["embedding"]["provider"],
                "rerank": config["rerank"]["provider"],
            },
            duration_ms=(time.perf_counter() - started) * 1000,
            source=source,
        )
        return results

    def query(
        self,
        question: str,
        retrieval_top_k: Optional[int] = None,
        final_top_k: Optional[int] = None,
        enable_llm_answer: Optional[bool] = None,
        source: str = "admin",
    ) -> Dict[str, Any]:
        import time

        from tcm_ai.rag.providers import invoke_llm, rerank_documents

        started = time.perf_counter()
        config = load_config()
        rag_cfg = config["rag"]
        retrieval_k = retrieval_top_k or int(rag_cfg.get("retrieval_top_k", 20))
        final_k = final_top_k or int(rag_cfg.get("final_top_k", 5))
        use_llm = enable_llm_answer if enable_llm_answer is not None else bool(
            rag_cfg.get("enable_llm_answer", True)
        )
        rerank_top_n = int(config["rerank"].get("top_n", final_k))

        retrieved = self.vector_index.search(question, top_k=retrieval_k)
        reranked = rerank_documents(config["rerank"], question, retrieved, top_n=max(final_k, rerank_top_n))
        for item in reranked:
            if "rerank_score" not in item:
                item["rerank_score"] = item.get("score", 0.0)
        context_blocks = []
        for i, item in enumerate(reranked[:final_k], start=1):
            source_path = item.get("file_path") or item.get("source") or "未知来源"
            context_blocks.append(
                f"[{i}] 标题: {item.get('title', '')}\n"
                f"来源: {source_path}\n"
                f"分类: {item.get('category', '')}\n"
                f"内容: {item.get('content', '')}"
            )
        context = "\n\n".join(context_blocks)

        answer = ""
        if use_llm and context:
            prompt = (
                "你是一位资深中医专家。请严格依据下列检索到的中医资料回答问题。\n"
                "若资料不足以回答，请明确说明，不要编造。\n\n"
                f"用户问题：{question}\n\n"
                f"检索资料：\n{context}\n\n"
                "请给出简洁、结构化的回答，并注明主要依据条目编号。"
            )
            answer = invoke_llm(config["llm"], prompt)
        elif use_llm and not context:
            answer = "未检索到相关知识，无法生成回答。请尝试重建向量索引或调整问题。"

        log_rag_event(
            "query",
            question,
            retrieved_count=len(retrieved),
            final_top_k=final_k,
            providers={
                "embedding": config["embedding"]["provider"],
                "llm": config["llm"]["provider"],
                "rerank": config["rerank"]["provider"],
            },
            duration_ms=(time.perf_counter() - started) * 1000,
            has_answer=bool(answer),
            answer_preview=answer,
            source=source,
        )

        duration_ms = (time.perf_counter() - started) * 1000
        return {
            "question": question,
            "answer": answer,
            "retrieved_count": len(retrieved),
            "retrieved": retrieved,
            "reranked": reranked[:final_k],
            "context": context,
            "duration_ms": round(duration_ms, 2),
            "token_estimate": max(len(answer) // 2, 0) if answer else 0,
            "providers": {
                "embedding": config["embedding"]["provider"],
                "llm": config["llm"]["provider"],
                "rerank": config["rerank"]["provider"],
            },
        }

    def rebuild_index(
        self,
        force: bool = False,
        progress_callback: Optional[Any] = None,
    ) -> Dict[str, Any]:
        self.vector_index.invalidate()
        return self.vector_index.build_index(force=force, progress_callback=progress_callback)
