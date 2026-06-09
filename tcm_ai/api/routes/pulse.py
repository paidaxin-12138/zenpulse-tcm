import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from tcm_ai.api.deps import get_diagnosis_service
from tcm_ai.api.public_access import ensure_public_pulse_allowed
from tcm_ai.api.schemas.pulse import PulseAnalyzeRequest, PulseAnalyzeResponse
from tcm_ai.api.wx_user_auth import get_optional_wx_user_id
from tcm_ai.core.http_errors import safe_client_message
from tcm_ai.core.jsonl_store import append_jsonl_record
from tcm_ai.core.paths import PROJECT_ROOT
from tcm_ai.domain.constants import DISCLAIMER
from tcm_ai.services.diagnosis_service import DiagnosisService

router = APIRouter(tags=["脉象"])

SESSIONS_PATH = os.path.join(PROJECT_ROOT, "data", "pulse_sessions.jsonl")


@router.post("/api/pulse/analyze", response_model=PulseAnalyzeResponse)
async def analyze_pulse(
    request: Request,
    payload: PulseAnalyzeRequest,
    wx_user_id: Optional[str] = Depends(get_optional_wx_user_id),
    diagnosis_service: DiagnosisService = Depends(get_diagnosis_service),
):
    ensure_public_pulse_allowed(request, wx_user_id)
    try:
        result = await asyncio.to_thread(
            diagnosis_service.analyze_pulse_request,
            payload.model_dump(),
        )
        if not result.success:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": result.error,
                    "message": result.description,
                    "quality": result.quality.to_dict(),
                },
            )
        body = result.to_dict()
        body["disclaimer"] = DISCLAIMER
        return PulseAnalyzeResponse(**body)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=safe_client_message(exc, public="脉象分析暂时不可用，请稍后重试"),
        ) from exc


@router.post("/api/pulse/sessions")
async def create_pulse_session(
    request: Request,
    payload: PulseAnalyzeRequest,
    wx_user_id: Optional[str] = Depends(get_optional_wx_user_id),
    diagnosis_service: DiagnosisService = Depends(get_diagnosis_service),
):
    ensure_public_pulse_allowed(request, wx_user_id)
    try:
        result = await asyncio.to_thread(
            diagnosis_service.analyze_pulse_request,
            payload.model_dump(),
        )
        session_id = str(uuid.uuid4())
        record = {
            "session_id": session_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "request": {
                "fs": payload.fs,
                "source": payload.source,
                "capability_level": payload.capability_level,
                "sample_count": len(payload.samples),
            },
            "result": result.to_dict(),
        }
        append_jsonl_record(SESSIONS_PATH, record)
        return {"session_id": session_id, "stored": True, "success": result.success}
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=safe_client_message(exc, public="脉象会话保存失败，请稍后重试"),
        ) from exc
