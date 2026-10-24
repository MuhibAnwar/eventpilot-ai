"""Optional HTTP Basic auth when APP_PASSWORD is set."""

from __future__ import annotations

import base64
import os
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        expected = os.environ.get("APP_PASSWORD")
        if not expected:
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Basic "):
            return Response(
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="EventPilot AI"'},
                content="Authentication required",
            )
        try:
            decoded = base64.b64decode(auth[6:]).decode("utf-8")
            _username, _, password = decoded.partition(":")
        except Exception:
            return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="EventPilot AI"'})

        if not secrets.compare_digest(password, expected):
            return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="EventPilot AI"'})

        return await call_next(request)
