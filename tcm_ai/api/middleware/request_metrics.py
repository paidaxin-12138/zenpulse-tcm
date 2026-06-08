"""记录 HTTP 请求计数供 Prometheus 导出。"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from tcm_ai.core.request_metrics import record_request, should_record_path


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if not should_record_path(path):
            return await call_next(request)
        response = await call_next(request)
        record_request(request.method, path, response.status_code)
        return response
