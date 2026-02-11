"""Correlation ID propagation middleware."""

import contextvars
from typing import Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default="N/A"
)


def generate_correlation_id() -> str:
    """Generate a unique correlation ID.

    Returns:
        16-character hexadecimal string.
    """
    return uuid4().hex[:16]


def get_correlation_id() -> str:
    """Get the current correlation ID from context.

    Returns:
        Current correlation ID or 'N/A' if not set.
    """
    return correlation_id_ctx.get()


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware that generates and propagates correlation IDs."""

    def __init__(self, app: Callable) -> None:
        """Initialize middleware."""
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with correlation ID."""
        incoming_id = request.headers.get("X-Correlation-ID")
        correlation_id = incoming_id or generate_correlation_id()

        correlation_id_ctx.set(correlation_id)

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id

        return response
