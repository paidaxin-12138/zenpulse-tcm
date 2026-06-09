"""Deprecated: use tcm_ai.knowledge.loader."""

import warnings

from tcm_ai.knowledge.loader import TCMAgentKnowledgeManager, TCMKnowledgeLoader

warnings.warn(
    "tcm_ai.ai.tcm_knowledge_loader is deprecated; import from tcm_ai.knowledge.loader",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["TCMAgentKnowledgeManager", "TCMKnowledgeLoader"]
