from typing import TYPE_CHECKING, Any, Optional

from tcm_ai.core.service_registry import (
    get_diagnosis_service as get_diagnosis_service,
    get_knowledge_service as get_knowledge_service,
    get_rag_pipeline as get_rag_pipeline,
    get_tcm_agent as get_tcm_agent,
    reset_ai_cache as reset_ai_cache,
)

if TYPE_CHECKING:
    from tcm_ai.adapters.stm.processor import STMDataProcessor
    from tcm_ai.adapters.vision.eye_detector import EyeDetector
    from tcm_ai.adapters.vision.face_detector import FaceDetector
    from tcm_ai.adapters.vision.tongue_detector import TongueDetector
    from tcm_ai.services.patient_service import PatientService
    from tcm_ai.services.rag_log_service import RAGLogService
    from tcm_ai.services.index_rebuild_service import IndexRebuildService
    from tcm_ai.services.system_service import SystemService
    from tcm_ai.services.vision_service import VisionService

_face_detector: Optional[Any] = None
_tongue_detector: Optional[Any] = None
_eye_detector: Optional[Any] = None
_vision_service: Optional[Any] = None
_patient_service: Optional[Any] = None
_system_service: Optional[Any] = None
_rag_log_service: Optional[Any] = None
_index_rebuild_service: Optional[Any] = None
_stm_processor: Optional[Any] = None
_vitals_service: Optional[Any] = None


def get_face_detector() -> "FaceDetector":
    global _face_detector
    if _face_detector is None:
        from tcm_ai.adapters.vision.face_detector import FaceDetector

        _face_detector = FaceDetector()
    return _face_detector


def get_tongue_detector() -> "TongueDetector":
    global _tongue_detector
    if _tongue_detector is None:
        from tcm_ai.adapters.vision.tongue_detector import TongueDetector

        _tongue_detector = TongueDetector()
    return _tongue_detector


def get_eye_detector() -> "EyeDetector":
    global _eye_detector
    if _eye_detector is None:
        from tcm_ai.adapters.vision.eye_detector import EyeDetector

        _eye_detector = EyeDetector()
    return _eye_detector


def get_vision_service() -> "VisionService":
    global _vision_service
    if _vision_service is None:
        from tcm_ai.services.vision_service import VisionService

        _vision_service = VisionService(
            face_detector=get_face_detector(),
            tongue_detector=get_tongue_detector(),
            eye_detector=get_eye_detector(),
        )
    return _vision_service


def get_patient_service() -> "PatientService":
    global _patient_service
    if _patient_service is None:
        from tcm_ai.services.patient_service import PatientService

        _patient_service = PatientService()
    return _patient_service


def get_system_service() -> "SystemService":
    global _system_service
    if _system_service is None:
        from tcm_ai.services.system_service import SystemService

        _system_service = SystemService()
    return _system_service


def get_rag_log_service() -> "RAGLogService":
    global _rag_log_service
    if _rag_log_service is None:
        from tcm_ai.services.rag_log_service import RAGLogService

        _rag_log_service = RAGLogService()
    return _rag_log_service


def get_index_rebuild_service() -> "IndexRebuildService":
    global _index_rebuild_service
    if _index_rebuild_service is None:
        from tcm_ai.services.index_rebuild_service import IndexRebuildService

        _index_rebuild_service = IndexRebuildService()
    return _index_rebuild_service


def get_stm_processor() -> "STMDataProcessor":
    global _stm_processor
    if _stm_processor is None:
        from tcm_ai.adapters.stm.processor import STMDataProcessor

        _stm_processor = STMDataProcessor()
    return _stm_processor


def get_vitals_service():
    global _vitals_service
    if _vitals_service is None:
        from tcm_ai.services.vitals_service import VitalsService

        _vitals_service = VitalsService()
    return _vitals_service
