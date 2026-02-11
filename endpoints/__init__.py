"""Endpoints package."""

from endpoints.health import router as health_router
from endpoints.metrics import router as metrics_router

__all__ = [
    "health_router",
    "metrics_router",
]
