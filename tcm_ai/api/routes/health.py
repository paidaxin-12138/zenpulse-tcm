# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import random

from fastapi import APIRouter

from tcm_ai.core.startup import check_python_packages, index_ready

router = APIRouter(tags=["健康指标"])


@router.get("/api/health")
def health_check():
    """存活探针：进程已启动即可。"""
    return {"ok": True}


@router.get("/api/ready")
def readiness_check():
    """就绪探针：向量索引与 RAG 依赖是否可用于诊断/检索。"""
    missing = check_python_packages()
    idx = index_ready()
    rag_deps_ok = len(missing) == 0
    ready = idx or not rag_deps_ok
    return {
        "ready": ready,
        "index_ready": idx,
        "rag_deps_ok": rag_deps_ok,
        "missing_packages": missing,
    }


@router.get("/api/health-metrics")
def get_health_metrics():
    return {
        "heart_rate": random.randint(60, 100),
        "pulse": random.randint(60, 100),
        "systolic": random.randint(90, 140),
        "diastolic": random.randint(60, 90),
    }
