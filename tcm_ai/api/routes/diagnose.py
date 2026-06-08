import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from tcm_ai.api.deps import get_diagnosis_service, get_vision_service
from tcm_ai.api.public_access import ensure_public_diagnose_allowed
from tcm_ai.api.schemas.diagnose import DiagnoseJsonRequest, DiagnoseResponse
from tcm_ai.core.http_errors import safe_client_message
from tcm_ai.services.diagnosis_service import DiagnosisService
from tcm_ai.services.vision_service import VisionService

router = APIRouter(tags=["诊断"])


def _build_stm_data(
    heart_rate: int,
    pulse: int,
    systolic: int,
    diastolic: int,
    age: Optional[int] = None,
    gender: Optional[str] = None,
) -> dict:
    return {
        "heart_rate": heart_rate,
        "pulse": pulse,
        "systolic_pressure": systolic,
        "diastolic_pressure": diastolic,
        "age": age,
        "gender": gender,
    }


@router.post("/api/diagnose", response_model=DiagnoseResponse)
async def diagnose_multipart(
    request: Request,
    tongue_image: UploadFile = File(None, description="舌苔照片"),
    face_image: UploadFile = File(None, description="面部照片"),
    eye_image: UploadFile = File(None, description="眼睛照片"),
    heart_rate: int = Form(..., description="心率"),
    pulse: int = Form(..., description="脉搏"),
    systolic: int = Form(..., description="收缩压"),
    diastolic: int = Form(..., description="舒张压"),
    age: Optional[int] = Form(default=None, description="年龄"),
    gender: Optional[str] = Form(default=None, description="性别"),
    vision_service: VisionService = Depends(get_vision_service),
    diagnosis_service: DiagnosisService = Depends(get_diagnosis_service),
):
    ensure_public_diagnose_allowed(request)
    try:
        if None in [heart_rate, pulse, systolic, diastolic]:
            raise HTTPException(status_code=400, detail="请提供完整的健康指标")

        face_cv = tongue_cv = eye_cv = None
        if face_image:
            face_cv = vision_service.decode_image(await face_image.read())
        if tongue_image:
            tongue_cv = vision_service.decode_image(await tongue_image.read())
        if eye_image:
            eye_cv = vision_service.decode_image(await eye_image.read())

        vision_data = await asyncio.to_thread(
            vision_service.analyze_from_images,
            face_cv=face_cv,
            tongue_cv=tongue_cv,
            eye_cv=eye_cv,
        )
        stm_data = _build_stm_data(heart_rate, pulse, systolic, diastolic, age, gender)
        return await asyncio.to_thread(diagnosis_service.run, vision_data, stm_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=safe_client_message(exc, public="诊断服务暂时不可用，请稍后重试"),
        ) from exc


@router.post("/api/diagnose/json", response_model=DiagnoseResponse)
async def diagnose_json(
    request: Request,
    payload: DiagnoseJsonRequest,
    vision_service: VisionService = Depends(get_vision_service),
    diagnosis_service: DiagnosisService = Depends(get_diagnosis_service),
):
    ensure_public_diagnose_allowed(request)
    try:
        face_cv = tongue_cv = eye_cv = None
        if payload.images:
            if payload.images.face:
                face_cv = vision_service.decode_base64_image(payload.images.face)
            if payload.images.tongue:
                tongue_cv = vision_service.decode_base64_image(payload.images.tongue)
            if payload.images.eye:
                eye_cv = vision_service.decode_base64_image(payload.images.eye)

        vision_data = await asyncio.to_thread(
            vision_service.analyze_from_images,
            face_cv=face_cv,
            tongue_cv=tongue_cv,
            eye_cv=eye_cv,
        )
        stm_data = _build_stm_data(
            payload.heart_rate,
            payload.pulse,
            payload.systolic,
            payload.diastolic,
            payload.age,
            payload.gender,
        )
        return await asyncio.to_thread(diagnosis_service.run, vision_data, stm_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=safe_client_message(exc, public="诊断服务暂时不可用，请稍后重试"),
        ) from exc
