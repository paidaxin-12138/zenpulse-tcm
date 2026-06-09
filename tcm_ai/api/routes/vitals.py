# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from tcm_ai.api.deps import get_vitals_service
from tcm_ai.api.public_access import ensure_public_vitals_allowed
from tcm_ai.api.schemas.vitals import VitalsAnalyzeRequest, VitalsAnalyzeResponse
from tcm_ai.api.wx_user_auth import get_optional_wx_user_id
from tcm_ai.core.http_errors import safe_client_message
from tcm_ai.domain.constants import DISCLAIMER
from tcm_ai.services.vitals_service import VitalsService

router = APIRouter(tags=["生理参数"])


@router.post("/api/vitals/analyze", response_model=VitalsAnalyzeResponse)
async def analyze_vitals(
    request: Request,
    payload: VitalsAnalyzeRequest,
    wx_user_id: Optional[str] = Depends(get_optional_wx_user_id),
    vitals_service: VitalsService = Depends(get_vitals_service),
):
    ensure_public_vitals_allowed(request, wx_user_id)
    try:
        result = await asyncio.to_thread(
            vitals_service.analyze_samples,
            payload.samples,
            payload.fs,
            payload.samples_ch2,
            payload.source,
        )
        if not result.success:
            raise HTTPException(
                status_code=422,
                detail={"error": result.error, "message": result.alerts[0] if result.alerts else result.error},
            )
        body = result.to_dict()
        body["disclaimer"] = DISCLAIMER
        return VitalsAnalyzeResponse(**body)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=safe_client_message(exc, public="生理参数分析暂时不可用，请稍后重试"),
        ) from exc
