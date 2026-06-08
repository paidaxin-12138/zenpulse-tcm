from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from tcm_ai.api.admin_auth import require_admin_role
from tcm_ai.core.http_errors import safe_client_message
from tcm_ai.api.deps import (
    get_index_rebuild_service,
    get_knowledge_service,
    get_patient_service,
    get_rag_log_service,
    get_rag_pipeline,
    get_system_service,
    reset_ai_cache,
)
from tcm_ai.api.schemas.admin import (
    ConfigUpdate,
    KnowledgeSearchRequest,
    KnowledgeUploadRequest,
    PatientCreate,
    PatientUpdate,
    ProviderTestRequest,
    RAGQueryRequest,
    VisitCreate,
)
from tcm_ai.core.config_store import (
    load_config,
    mask_config,
    merge_config_update,
    regenerate_admin_api_key,
    save_config,
)
from tcm_ai.core.security_check import validate_security_config
from tcm_ai.core.llm_setup import get_llm_setup_report, try_pull_ollama_model
from tcm_ai.services.index_rebuild_service import IndexRebuildService
from tcm_ai.services.knowledge_service import KnowledgeService
from tcm_ai.services.patient_service import PatientService
from tcm_ai.services.rag_log_service import RAGLogService
from tcm_ai.services.system_service import SystemService

router = APIRouter(prefix="/api/admin", tags=["管理端"])

require_admin_key = require_admin_role("viewer")
require_editor = require_admin_role("editor")
require_super_admin = require_admin_role("admin")


@router.get("/me")
def admin_me(role: str = Depends(require_admin_key)) -> Dict[str, str]:
    return {"role": role}


@router.get("/config")
def get_admin_config(_: None = Depends(require_admin_key)) -> Dict[str, Any]:
    return mask_config(load_config())


@router.get("/dashboard")
def admin_dashboard(
    _: None = Depends(require_admin_key),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    system_service: SystemService = Depends(get_system_service),
    log_service: RAGLogService = Depends(get_rag_log_service),
    rebuild_service: IndexRebuildService = Depends(get_index_rebuild_service),
) -> Dict[str, Any]:
    cfg = mask_config(load_config())
    return {
        "knowledge": knowledge_service.stats(),
        "index": system_service.index_status(),
        "rebuild": rebuild_service.get_status(),
        "rag_stats": log_service.stats(),
        "models": {
            "embedding": {
                "provider": cfg["embedding"]["provider"],
                "model": cfg["embedding"]["model"],
            },
            "llm": {
                "provider": cfg["llm"]["provider"],
                "model": cfg["llm"]["model"],
            },
            "rerank": {
                "provider": cfg["rerank"]["provider"],
                "model": cfg["rerank"]["model"],
            },
        },
    }


@router.put("/config")
def update_admin_config(
    payload: ConfigUpdate,
    _: str = Depends(require_super_admin),
) -> Dict[str, Any]:
    current = load_config()
    updated = merge_config_update(current, payload.model_dump(exclude_none=True))
    errors = [m for m in validate_security_config(updated) if m.startswith("ERROR:")]
    if errors:
        raise HTTPException(
            status_code=400,
            detail=errors[0].replace("ERROR: ", ""),
        )
    save_config(updated)
    reset_ai_cache()
    return mask_config(updated)


@router.post("/config/regenerate-key")
def regenerate_key(_: str = Depends(require_super_admin)) -> Dict[str, str]:
    new_key = regenerate_admin_api_key()
    reset_ai_cache()
    return {"admin_api_key": new_key}


@router.get("/system/llm-setup")
def admin_llm_setup(_: str = Depends(require_admin_key)) -> Dict[str, Any]:
    return get_llm_setup_report()


@router.post("/system/llm-pull")
def admin_llm_pull(_: str = Depends(require_super_admin)) -> Dict[str, Any]:
    model = (load_config().get("llm") or {}).get("model", "")
    result = try_pull_ollama_model(str(model))
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error", "拉取失败"))
    return result


@router.get("/system/dev-hints")
def admin_dev_hints(_: str = Depends(require_admin_key)) -> Dict[str, Any]:
    from tcm_ai.api.routes.system_public import public_dev_hints

    return public_dev_hints()


@router.post("/rag/query")
def rag_query(
    payload: RAGQueryRequest,
    _: str = Depends(require_editor),
) -> Dict[str, Any]:
    try:
        return get_rag_pipeline().query(
            question=payload.question,
            retrieval_top_k=payload.retrieval_top_k,
            final_top_k=payload.final_top_k,
            enable_llm_answer=payload.enable_llm_answer,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=safe_client_message(exc, public="RAG 查询失败，请稍后重试"),
        ) from exc
def rebuild_index(
    force: bool = False,
    _: str = Depends(require_super_admin),
) -> Dict[str, Any]:
    """同步重建（兼容脚本）；大数据量请用 /rag/rebuild-index/async。"""
    try:
        return get_rag_pipeline().rebuild_index(force=force)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=safe_client_message(exc, public="索引重建失败，请稍后重试"),
        ) from exc


@router.post("/rag/rebuild-index/async")
def rebuild_index_async(
    force: bool = False,
    _: str = Depends(require_editor),
    rebuild_service: IndexRebuildService = Depends(get_index_rebuild_service),
) -> Dict[str, Any]:
    try:
        return rebuild_service.start(force=force)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/rag/rebuild-index/status")
def rebuild_index_status(
    _: None = Depends(require_admin_key),
    rebuild_service: IndexRebuildService = Depends(get_index_rebuild_service),
) -> Dict[str, Any]:
    return rebuild_service.get_status()


@router.get("/knowledge/stats")
def knowledge_stats(
    _: None = Depends(require_admin_key),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
) -> Dict[str, Any]:
    return knowledge_service.stats()


@router.get("/knowledge/files")
def knowledge_files(
    _: None = Depends(require_admin_key),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
) -> Dict[str, Any]:
    return {"files": knowledge_service.list_files()}


@router.post("/knowledge/search")
def knowledge_search(
    payload: KnowledgeSearchRequest,
    _: None = Depends(require_admin_key),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
) -> Dict[str, Any]:
    return {
        "query": payload.query,
        "results": knowledge_service.search_keywords(payload.query, payload.top_k),
    }


@router.post("/knowledge/upload")
def knowledge_upload(
    payload: KnowledgeUploadRequest,
    _: str = Depends(require_editor),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
) -> Dict[str, Any]:
    try:
        result = knowledge_service.upload_text(payload.path, payload.content, payload.overwrite)
        reset_ai_cache()
        return result
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/knowledge/import-files")
async def knowledge_import_files(
    files: List[UploadFile] = File(...),
    subdir: str = Form("imports"),
    overwrite: bool = Form(False),
    _: str = Depends(require_editor),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
) -> Dict[str, Any]:
    imported: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    for upload in files:
        if not upload.filename:
            continue
        try:
            content = await upload.read()
            result = knowledge_service.upload_file(
                upload.filename, content, subdir=subdir, overwrite=overwrite
            )
            imported.append(result)
        except FileExistsError as exc:
            errors.append({"file": upload.filename, "error": str(exc)})
        except ValueError as exc:
            errors.append({"file": upload.filename, "error": str(exc)})
    if imported:
        reset_ai_cache()
    return {"imported": imported, "errors": errors, "count": len(imported)}


@router.delete("/knowledge/files/{file_path:path}")
def knowledge_delete(
    file_path: str,
    _: str = Depends(require_editor),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
) -> Dict[str, str]:
    try:
        result = knowledge_service.delete_file(file_path)
        reset_ai_cache()
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/knowledge/case-library/stats")
def case_library_stats(
    _: None = Depends(require_admin_key),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
) -> Dict[str, Any]:
    return knowledge_service.case_library_stats()


@router.get("/knowledge/case-library")
def search_case_library(
    limit: int = 50,
    offset: int = 0,
    q: str = "",
    _: None = Depends(require_admin_key),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
) -> Dict[str, Any]:
    return knowledge_service.list_case_library(limit=limit, offset=offset, q=q)


@router.get("/knowledge/case-library/{case_id}")
def get_case_library_entry(
    case_id: str,
    _: None = Depends(require_admin_key),
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
) -> Dict[str, Any]:
    try:
        return knowledge_service.get_case_library_entry(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"病例不存在: {case_id}") from exc


@router.get("/patients")
def list_patients(
    limit: int = 50,
    offset: int = 0,
    q: str = "",
    _: None = Depends(require_admin_key),
    patient_service: PatientService = Depends(get_patient_service),
) -> Dict[str, Any]:
    return patient_service.list_patients(limit=limit, offset=offset, q=q)


@router.get("/patients/{patient_id}")
def get_patient(
    patient_id: str,
    _: None = Depends(require_admin_key),
    patient_service: PatientService = Depends(get_patient_service),
) -> Dict[str, Any]:
    try:
        return patient_service.get_patient(patient_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"患者不存在: {patient_id}") from exc


@router.post("/patients")
def create_patient(
    payload: PatientCreate,
    _: str = Depends(require_editor),
    patient_service: PatientService = Depends(get_patient_service),
) -> Dict[str, Any]:
    try:
        return patient_service.create_patient(payload.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/patients/{patient_id}")
def update_patient(
    patient_id: str,
    payload: PatientUpdate,
    _: str = Depends(require_editor),
    patient_service: PatientService = Depends(get_patient_service),
) -> Dict[str, Any]:
    try:
        return patient_service.update_patient(
            patient_id, payload.model_dump(exclude_none=True)
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"患者不存在: {patient_id}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/patients/{patient_id}")
def delete_patient(
    patient_id: str,
    _: str = Depends(require_editor),
    patient_service: PatientService = Depends(get_patient_service),
) -> Dict[str, str]:
    try:
        return patient_service.delete_patient(patient_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"患者不存在: {patient_id}") from exc


@router.get("/patients/{patient_id}/visits")
def list_patient_visits(
    patient_id: str,
    _: None = Depends(require_admin_key),
    patient_service: PatientService = Depends(get_patient_service),
) -> Dict[str, Any]:
    try:
        return patient_service.list_visits(patient_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"患者不存在: {patient_id}") from exc


@router.post("/patients/{patient_id}/visits")
def create_patient_visit(
    patient_id: str,
    payload: VisitCreate,
    _: str = Depends(require_editor),
    patient_service: PatientService = Depends(get_patient_service),
) -> Dict[str, Any]:
    try:
        return patient_service.create_visit(
            patient_id, payload.model_dump(exclude_none=True)
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"患者不存在: {patient_id}") from exc


@router.get("/system/index-status")
def index_status(
    _: None = Depends(require_admin_key),
    system_service: SystemService = Depends(get_system_service),
) -> Dict[str, Any]:
    return system_service.index_status()


@router.post("/system/test-models")
def test_models(
    _: str = Depends(require_editor),
    system_service: SystemService = Depends(get_system_service),
) -> Dict[str, Any]:
    return system_service.test_models()


@router.post("/system/test-embedding")
def test_embedding(
    payload: Optional[ProviderTestRequest] = None,
    _: str = Depends(require_editor),
    system_service: SystemService = Depends(get_system_service),
) -> Dict[str, Any]:
    override = payload.model_dump(exclude_none=True) if payload else None
    try:
        return system_service.test_embedding(override)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/system/test-llm")
def test_llm(
    payload: Optional[ProviderTestRequest] = None,
    _: str = Depends(require_editor),
    system_service: SystemService = Depends(get_system_service),
) -> Dict[str, Any]:
    override = payload.model_dump(exclude_none=True) if payload else None
    try:
        return system_service.test_llm(override)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/system/test-rerank")
def test_rerank(
    payload: Optional[ProviderTestRequest] = None,
    _: str = Depends(require_editor),
    system_service: SystemService = Depends(get_system_service),
) -> Dict[str, Any]:
    override = payload.model_dump(exclude_none=True) if payload else None
    try:
        return system_service.test_rerank(override)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/rag/logs/stats")
def rag_log_stats(
    _: None = Depends(require_admin_key),
    log_service: RAGLogService = Depends(get_rag_log_service),
) -> Dict[str, Any]:
    return log_service.stats()


@router.get("/rag/logs")
def rag_logs(
    limit: int = 50,
    offset: int = 0,
    source: Optional[str] = None,
    kind: Optional[str] = None,
    _: None = Depends(require_admin_key),
    log_service: RAGLogService = Depends(get_rag_log_service),
) -> Dict[str, Any]:
    return log_service.list_logs(limit=limit, offset=offset, source=source, kind=kind)


@router.delete("/rag/logs")
def clear_rag_logs(
    _: str = Depends(require_editor),
    log_service: RAGLogService = Depends(get_rag_log_service),
) -> Dict[str, str]:
    return log_service.clear()
