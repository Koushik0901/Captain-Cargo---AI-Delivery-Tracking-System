"""Webhook payload validation middleware."""

from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse

from models.webhook import WebhookPayload
from utils.logger import logger
from middleware.correlation import get_correlation_id


class ValidationMiddleware(BaseHTTPMiddleware):
    """Middleware that validates incoming webhook payloads."""

    def __init__(self, app: Callable) -> None:
        """Initialize middleware."""
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate request body if content-type is application/json."""
        if request.headers.get("content-type") != "application/json":
            return await call_next(request)

        try:
            body = await request.json()
        except Exception:
            return PlainTextResponse(
                content="Invalid JSON payload",
                status_code=400,
            )

        try:
            WebhookPayload.model_validate(body)
        except Exception as e:
            correlation_id = get_correlation_id()
            logger.warning(
                f"Webhook validation failed",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(e),
                },
            )
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "Validation failed",
                    "details": str(e),
                },
                status_code=422,
            )

        return await call_next(request)
