__all__ = [
    "TCMAgent",
    "DiagnosisService",
    "VisionService",
    "KnowledgeService",
    "SystemService",
]


def __getattr__(name: str):
    if name == "DiagnosisService":
        from tcm_ai.services.diagnosis_service import DiagnosisService

        return DiagnosisService
    if name == "KnowledgeService":
        from tcm_ai.services.knowledge_service import KnowledgeService

        return KnowledgeService
    if name == "SystemService":
        from tcm_ai.services.system_service import SystemService

        return SystemService
    if name == "TCMAgent":
        from tcm_ai.services.tcm_agent import TCMAgent

        return TCMAgent
    if name == "VisionService":
        from tcm_ai.services.vision_service import VisionService

        return VisionService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
