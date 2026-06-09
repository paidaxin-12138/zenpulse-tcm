import logging
import os
from typing import Any, Dict, List, Optional

from tcm_ai.core.paths import KNOWLEDGE_DIR
from tcm_ai.core.settings import get_settings
from tcm_ai.domain.fusion import FusionEngine
from tcm_ai.domain.rules import RuleEngine
from tcm_ai.knowledge.loader import TCMAgentKnowledgeManager
from tcm_ai.rag.pipeline import RAGPipeline
from tcm_ai.rag.providers import invoke_llm

logger = logging.getLogger(__name__)


class TCMAgent:
    """中医诊断编排器：RAG 检索 + LLM 推理 + 规则 fallback。"""

    def __init__(self, rag_pipeline: Optional[RAGPipeline] = None):
        config = get_settings()
        self.model = config["llm"]["model"]
        self.rag_pipeline = rag_pipeline or RAGPipeline()
        self.fusion_engine = FusionEngine()
        self.rule_engine = RuleEngine()
        self.knowledge_manager: Optional[TCMAgentKnowledgeManager] = None
        self._knowledge_loaded = False

    def _ensure_knowledge_manager(self) -> None:
        if self.knowledge_manager is None:
            self.knowledge_manager = TCMAgentKnowledgeManager(KNOWLEDGE_DIR)
        if not self._knowledge_loaded:
            self.knowledge_manager.load_all_knowledge()
            self._knowledge_loaded = True

    def _search_related_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        try:
            results = self.rag_pipeline.search_knowledge(query, top_k=top_k)
            if results:
                return results
        except Exception as exc:
            logger.warning("向量搜索失败: %s，回退到关键词搜索", exc)

        self._ensure_knowledge_manager()
        if self.knowledge_manager:
            return self.knowledge_manager.search_knowledge(query, top_k)
        return []

    def get_tcm_diagnosis(self, vision_data: Dict[str, Any], stm_data: Dict[str, float]) -> Dict[str, str]:
        try:
            config = get_settings()
            processed_vision = FusionEngine.process_vision_data(vision_data)
            processed_stm = FusionEngine.process_stm_data(stm_data)
            fusion_data = FusionEngine.fuse(processed_vision, processed_stm)
            diagnosis_query = FusionEngine.summarize_fusion_data(fusion_data)

            related_knowledge = self._search_related_knowledge(diagnosis_query)
            knowledge_context = "\n\n相关中医知识参考：\n"
            if related_knowledge:
                for i, knowledge in enumerate(related_knowledge):
                    source_info = knowledge.get("source", "未知来源")
                    if knowledge.get("file_path"):
                        source_info = os.path.basename(knowledge["file_path"])
                    if knowledge.get("section"):
                        source_info += f" (章节: {knowledge['section']})"
                    knowledge_context += (
                        f"{i+1}. {knowledge['title']} (来源: {source_info})\n"
                        f"   {knowledge['content']}\n"
                    )
            else:
                knowledge_context += "无相关知识参考"

            prompt = FusionEngine.create_fusion_diagnosis_prompt(fusion_data, knowledge_context)
            diagnosis_content = invoke_llm(config["llm"], prompt).strip()
            if not diagnosis_content:
                raise ValueError("LLM响应为空")

            fusion_summary = FusionEngine.summarize_fusion_data(fusion_data)
            return {
                "diagnosis": diagnosis_content,
                "source": "中医智能诊断系统(LLM模式)",
                "fusion_data": fusion_data,
                "fusion_summary": fusion_summary,
                "diagnosis_mode": "llm",
            }
        except Exception as exc:
            logger.warning("无法使用 LLM 进行诊断: %s，降级为规则引擎", exc)
            processed_vision = FusionEngine.process_vision_data(vision_data)
            processed_stm = FusionEngine.process_stm_data(stm_data)
            fusion_data = FusionEngine.fuse(processed_vision, processed_stm)
            result = RuleEngine.diagnose(vision_data, stm_data)
            result["fusion_data"] = fusion_data
            result["fusion_summary"] = FusionEngine.summarize_fusion_data(fusion_data)
            result["diagnosis_mode"] = "rule"
            result["llm_fallback_reason"] = str(exc)
            result["source"] = "中医智能诊断系统(规则模式 · LLM 不可用)"
            return result

    def get_tcm_suggestions(self, diagnosis: str) -> Dict[str, List[str]]:
        try:
            config = get_settings()
            prompt = f"""
根据以下中医诊断结果，给出具体的生活调理、饮食建议和中药推荐：

诊断结果：{diagnosis}

请按照以下格式给出建议：
1. 生活调理：
2. 饮食建议：
3. 中药推荐：

请用通俗易懂的语言进行描述。
"""
            suggestions_content = invoke_llm(config["llm"], prompt)
            return {"suggestions": suggestions_content, "source": "中医智能建议系统"}
        except Exception as exc:
            return {
                "suggestions": f"建议生成过程中出现错误: {exc}\n请检查 LLM 配置（Ollama 或 API Key）",
                "source": "中医智能建议系统",
            }
