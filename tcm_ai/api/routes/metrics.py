# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""管理端运维指标（JSON，供监控采集）。"""

from __future__ import annotations

import os
import time
from typing import Any, Dict

from fastapi import APIRouter, Depends

from tcm_ai.api.admin_auth import require_admin_role
from tcm_ai.core.rate_limit import redis_degraded
from tcm_ai.core.redis_client import redis_url
from tcm_ai.core.runtime import get_tcm_env, is_production
from tcm_ai.core.startup import check_python_packages, index_ready

router = APIRouter(prefix="/api/admin", tags=["管理端"])

_started_at = time.time()

require_admin_key = require_admin_role("viewer")


@router.get("/metrics")
def admin_metrics(_: str = Depends(require_admin_key)) -> Dict[str, Any]:
    missing = check_python_packages()
    return {
        "uptime_seconds": round(time.time() - _started_at, 1),
        "tcm_env": get_tcm_env(),
        "production": is_production(),
        "index_ready": index_ready(),
        "rag_deps_ok": len(missing) == 0,
        "missing_packages": missing,
        "history_backend": os.environ.get("TCM_HISTORY_BACKEND", "json"),
        "redis_rate_limit": bool(redis_url()),
        "redis_rate_limit_degraded": redis_degraded(),
        "workers_hint": "多 worker 部署请设置 TCM_REDIS_URL",
    }
