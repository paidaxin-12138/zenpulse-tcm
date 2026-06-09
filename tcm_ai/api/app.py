# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from tcm_ai.api.middleware.request_metrics import RequestMetricsMiddleware
from tcm_ai.api.middleware.security_headers import SecurityHeadersMiddleware
from tcm_ai.api.routes.admin import router as admin_router
from tcm_ai.api.routes.diagnose import router as diagnose_router
from tcm_ai.api.routes.health import router as health_router
from tcm_ai.api.routes.history import router as history_router
from tcm_ai.api.routes.knowledge import router as knowledge_router
from tcm_ai.api.routes.admin_session import router as admin_session_router
from tcm_ai.api.routes.metrics import router as metrics_router
from tcm_ai.api.routes.pages import router as pages_router
from tcm_ai.api.routes.pulse import router as pulse_router
from tcm_ai.api.routes.vitals import router as vitals_router
from tcm_ai.api.routes.prometheus_metrics import router as prometheus_router
from tcm_ai.api.routes.system_public import router as system_public_router
from tcm_ai.api.routes.wx_auth import router as wx_auth_router
from tcm_ai.core.logging_config import configure_logging
from tcm_ai.core.runtime import is_production
from tcm_ai.core.security_check import enforce_security_config
from tcm_ai.core.settings import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    import asyncio

    configure_logging()
    from tcm_ai.core.startup import run_startup_checks

    enforce_security_config(get_settings())
    report = await asyncio.to_thread(run_startup_checks, auto_build_index=True)
    if report.get("missing_packages"):
        print("⚠ 缺少 RAG 依赖:", ", ".join(report["missing_packages"]))
        print("  → pip install -r requirements.txt")
    elif report.get("index") == "built":
        print(f"✓ 向量索引已自动构建 ({report.get('chunks')} chunks)")
    if report.get("ollama_warning"):
        print("⚠", report["ollama_warning"])
        print("  → 多模态 LLM 诊断将降级为规则引擎")
    yield


def create_app() -> FastAPI:
    config = get_settings()
    cors_origins = config.get("server", {}).get("cors_origins") or [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]
    allow_credentials = "*" not in cors_origins

    app = FastAPI(
        title="中医智能诊断系统",
        description="基于中医知识库的智能诊断 API",
        version="2.1.0",
        lifespan=lifespan,
        docs_url=None if is_production() else "/docs",
        redoc_url=None if is_production() else "/redoc",
        openapi_url=None if is_production() else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestMetricsMiddleware)

    app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
    app.mount("/admin-static", StaticFiles(directory="admin"), name="admin-static")

    app.include_router(pages_router)
    app.include_router(health_router)
    app.include_router(system_public_router)
    app.include_router(diagnose_router)
    app.include_router(pulse_router)
    app.include_router(vitals_router)
    app.include_router(history_router)
    app.include_router(knowledge_router)
    app.include_router(admin_router)
    app.include_router(admin_session_router)
    app.include_router(metrics_router)
    app.include_router(prometheus_router)
    app.include_router(wx_auth_router)

    return app


app = create_app()
