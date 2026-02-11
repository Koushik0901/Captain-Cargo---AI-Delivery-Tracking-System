"""Metrics endpoint (JSON format)."""

from fastapi import APIRouter
from typing import Any

from services.cache import DeliveryCache


router = APIRouter(tags=["metrics"])


def get_metrics() -> dict[str, Any]:
    """Collect metrics.

    Returns:
        Metrics dict with counters and gauges.
    """
    return {
        "requests_total": 0,
        "errors_total": 0,
        "cache_hits_total": 0,
        "cache_misses_total": 0,
        "cache_size": 0,
        "cache_hit_rate": 0.0,
        "latency_ms_p50": 0.0,
        "latency_ms_p95": 0.0,
    }


@router.get("/metrics")
async def metrics() -> dict[str, Any]:
    """Metrics endpoint (JSON format).

    Returns:
        JSON metrics dict.
    """
    return get_metrics()
