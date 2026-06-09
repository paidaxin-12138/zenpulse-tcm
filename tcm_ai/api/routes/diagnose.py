import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from tcm_ai.api.deps import get_diagnosis_service, get_vision_service
from tcm_ai.api.public_access import ensure_public_diagnose_allowed
from tcm_ai.api.schemas.diagnose import DiagnoseJsonRequest, DiagnoseResponse
from tcm_ai.api.wx_user_auth import get_optional_wx_user_id
from tcm_ai.core.http_errors import safe_client_message
from tcm_ai.domain.vitals.constants import VITALS_MAX_SAMPLES
from tcm_ai.services.diagnosis_service import DiagnosisService
from tcm_ai.services.vision_service import VisionService

router = APIRouter(tags=["诊断"])


def _validate_vitals_samples(
    pulse_waveform: Optional[list],
    max30102_samples_ch2: Optional[list] = None,
) -> None:
    if pulse_waveform is not None and len(pulse_waveform) > VITALS_MAX_SAMPLES:
        raise HTTPException(
            status_code=422,
            detail=f"波形点数不得超过 {VITALS_MAX_SAMPLES}",
        )
    if max30102_samples_ch2 is not None and len(max30102_samples_ch2) > VITALS_MAX_SAMPLES:
        raise HTTPException(
            status_code=422,
            detail=f"CH2 波形点数不得超过 {VITALS_MAX_SAMPLES}",
        )


def _build_stm_data(
    heart_rate: int,
    pulse: int,
    systolic: int,
    diastolic: int,
    age: Optional[int] = None,
    gender: Optional[str] = None,
    pulse_waveform: Optional[list] = None,
    pulse_fs: Optional[float] = None,
    pulse_source: Optional[str] = None,
    spo2: Optional[float] = None,
    max30102_samples_ch2: Optional[list] = None,
    vitals_assessment: Optional[dict] = None,
) -> dict:
    data = {
        "heart_rate": heart_rate,
        "pulse": pulse,
        "systolic_pressure": systolic,
        "diastolic_pressure": diastolic,
        "age": age,
        "gender": gender,
    }
    if pulse_waveform is not None:
        data["pulse_waveform"] = pulse_waveform
    if max30102_samples_ch2 is not None:
        data["max30102_samples_ch2"] = max30102_samples_ch2
    if pulse_fs is not None:
        data["pulse_fs"] = pulse_fs
    if pulse_source is not None:
        data["pulse_source"] = pulse_source
    if spo2 is not None:
        data["spo2"] = spo2
    if vitals_assessment is not None:
        data["vitals_assessment"] = vitals_assessment
    return data


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
    pulse_waveform_json: Optional[str] = Form(default=None, description="脉搏波形 JSON 数组"),
    max30102_samples_ch2_json: Optional[str] = Form(default=None, description="MAX30102 CH2 JSON 数组"),
    vitals_assessment_json: Optional[str] = Form(default=None, description="已分析 vitals_assessment JSON"),
    pulse_fs: Optional[float] = Form(default=None, description="脉搏采样率 Hz"),
    pulse_source: Optional[str] = Form(default=None, description="脉搏数据来源"),
    spo2: Optional[float] = Form(default=None, description="血氧（可选）"),
    wx_user_id: Optional[str] = Depends(get_optional_wx_user_id),
    vision_service: VisionService = Depends(get_vision_service),
    diagnosis_service: DiagnosisService = Depends(get_diagnosis_service),
):
    ensure_public_diagnose_allowed(request, wx_user_id)
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
        pulse_waveform = None
        max30102_samples_ch2 = None
        vitals_assessment = None
        if pulse_waveform_json:
            try:
                pulse_waveform = json.loads(pulse_waveform_json)
                if not isinstance(pulse_waveform, list):
                    raise ValueError("pulse_waveform_json 必须是数组")
            except (json.JSONDecodeError, ValueError) as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        if max30102_samples_ch2_json:
            try:
                max30102_samples_ch2 = json.loads(max30102_samples_ch2_json)
                if not isinstance(max30102_samples_ch2, list):
                    raise ValueError("max30102_samples_ch2_json 必须是数组")
            except (json.JSONDecodeError, ValueError) as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        if vitals_assessment_json:
            try:
                vitals_assessment = json.loads(vitals_assessment_json)
                if not isinstance(vitals_assessment, dict):
                    raise ValueError("vitals_assessment_json 必须是对象")
            except (json.JSONDecodeError, ValueError) as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        _validate_vitals_samples(pulse_waveform, max30102_samples_ch2)

        stm_data = _build_stm_data(
            heart_rate,
            pulse,
            systolic,
            diastolic,
            age,
            gender,
            pulse_waveform,
            pulse_fs,
            pulse_source,
            spo2,
            max30102_samples_ch2,
            vitals_assessment,
        )
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
    wx_user_id: Optional[str] = Depends(get_optional_wx_user_id),
    vision_service: VisionService = Depends(get_vision_service),
    diagnosis_service: DiagnosisService = Depends(get_diagnosis_service),
):
    ensure_public_diagnose_allowed(request, wx_user_id)
    try:
        _validate_vitals_samples(payload.pulse_waveform, payload.max30102_samples_ch2)
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
            payload.pulse_waveform,
            payload.pulse_fs,
            payload.pulse_source,
            payload.spo2,
            payload.max30102_samples_ch2,
            payload.vitals_assessment,
        )
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
