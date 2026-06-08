"""HTTP 安全响应头（Admin / 静态页）。"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_COMMON_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(self), microphone=(), geolocation=()",
}

_ADMIN_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://fonts.googleapis.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "img-src 'self' data: https:; "
    "connect-src 'self'; "
    "frame-ancestors 'self'; "
    "base-uri 'self'"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for key, value in _COMMON_HEADERS.items():
            response.headers.setdefault(key, value)
        path = request.url.path
        if path.startswith("/admin") or path.startswith("/admin-static"):
            response.headers.setdefault("Content-Security-Policy", _ADMIN_CSP)
        return response
