"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response."""

    status: str


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    status: str
    dependencies: dict


@router.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    """Liveness check.

    Returns:
        HealthResponse with status "ok".
    """
    return HealthResponse(status="ok")


@router.get("/readyz", response_model=ReadinessResponse)
async def readyz() -> ReadinessResponse:
    """Readiness check.

    Returns:
        ReadinessResponse with dependency status.
    """
    return ReadinessResponse(
        status="ready",
        dependencies={"healthy": True},
    )
