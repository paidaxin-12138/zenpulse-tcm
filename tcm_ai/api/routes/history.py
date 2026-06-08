from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from tcm_ai.api.wx_user_auth import require_wx_user_id
from tcm_ai.services.history_service import DiagnosisHistoryService

router = APIRouter(prefix="/api/diagnosis/history", tags=["诊断历史"])

_service = DiagnosisHistoryService()


@router.get("")
def list_history(
    limit: int = 50,
    user_id: str = Depends(require_wx_user_id),
) -> Dict[str, Any]:
    items = _service.list_entries(limit=limit, user_id=user_id)
    return {"total": len(items), "entries": items, "scoped": True}


@router.get("/{entry_id}")
def get_history_entry(
    entry_id: str,
    user_id: str = Depends(require_wx_user_id),
) -> Dict[str, Any]:
    entry = _service.get_entry(entry_id, user_id=user_id)
    if not entry:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"entry": entry, "scoped": True}


@router.post("")
def save_history(
    payload: Dict[str, Any],
    user_id: str = Depends(require_wx_user_id),
) -> Dict[str, Any]:
    detail = payload.get("detail")
    has_summary = payload.get("syndrome") or payload.get("diagnosis") or payload.get("summary")
    has_detail = isinstance(detail, dict) and bool(detail)
    if not has_summary and not has_detail:
        raise HTTPException(status_code=400, detail="请提供 syndrome、diagnosis、summary 或 detail")
    entry = _service.add_entry(payload, user_id=user_id)
    return {"ok": True, "entry": entry}


@router.delete("")
def clear_history(user_id: str = Depends(require_wx_user_id)) -> Dict[str, Any]:
    removed = _service.clear(user_id=user_id)
    return {"ok": True, "removed": removed}


@router.delete("/{entry_id}")
def delete_history_entry(
    entry_id: str,
    user_id: str = Depends(require_wx_user_id),
) -> Dict[str, Any]:
    if not _service.delete_entry(entry_id, user_id=user_id):
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"ok": True}
