import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings

OPEN_PATHS = {"/api/health", "/api/config"}


class SecurityMiddleware(BaseHTTPMiddleware):
    """Optional API-key auth + per-client sliding-window rate limit (per process)."""

    def __init__(self, app):
        super().__init__(app)
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        s = get_settings()
        path = request.url.path
        if request.method == "OPTIONS" or not path.startswith("/api"):
            return await call_next(request)
        if s.api_key and path not in OPEN_PATHS:
            supplied = request.headers.get("x-api-key") or request.query_params.get("api_key")
            if supplied != s.api_key:
                return JSONResponse({"detail": "Invalid or missing API key"}, status_code=401)
        if s.rate_limit_per_minute > 0 and "/stream" not in path:
            client = request.headers.get("x-forwarded-for", request.client.host if request.client else "?")
            q, now = self.hits[client], time.monotonic()
            while q and q[0] < now - 60:
                q.popleft()
            if len(q) >= s.rate_limit_per_minute:
                return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429,
                                    headers={"Retry-After": "10"})
            q.append(now)
        return await call_next(request)
