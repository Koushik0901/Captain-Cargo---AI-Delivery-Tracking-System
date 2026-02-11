"""Captain Cargo - Production-Grade Voice Agent for Delivery Tracking.

This FastAPI application handles Vapi webhook calls for delivery status inquiries.
"""

import contextlib
import json
import os
import signal
import sys
import time
from typing import Any, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from models.delivery import Delivery
from models.webhook import WebhookPayload
from services.cache import DeliveryCache
from services.response_builder import ResponseBuilder
from services.sanity_client import SanityClient
from utils.config import Config, validate_config
from utils.logger import logger, log_request
from utils.normalization import normalize_tracking_id
from middleware.correlation import (
    correlation_id_ctx,
    generate_correlation_id,
    CorrelationMiddleware,
)
from endpoints.health import router as health_router
from endpoints.metrics import router as metrics_router


def create_app(config: Optional[Config] = None) -> FastAPI:
    """Create and configure FastAPI application.

    Args:
        config: Optional Config object for testing.

    Returns:
        Configured FastAPI app.
    """
    if config is None:
        config = validate_config()

    app = FastAPI(
        title="Captain Cargo - Voice Agent Delivery Tracking",
        description="Production-grade Vapi webhook handler for delivery tracking",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(CorrelationMiddleware)

    sanity_client = SanityClient(config)
    delivery_cache = DeliveryCache(ttl_seconds=config.CACHE_TTL)
    response_builder = ResponseBuilder()

    request_count = 0
    error_count = 0

    def get_metrics() -> dict[str, Any]:
        """Get current metrics."""
        nonlocal request_count, error_count
        cache_stats = delivery_cache.get_stats()
        return {
            "requests_total": request_count,
            "errors_total": error_count,
            "cache_hits_total": cache_stats["hits"],
            "cache_misses_total": cache_stats["misses"],
            "cache_size": cache_stats["size"],
            "cache_hit_rate": cache_stats["hit_rate"],
        }

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next: Any) -> Response:
        """Track request metrics."""
        nonlocal request_count, error_count
        start_time = time.time()

        correlation_id = correlation_id_ctx.get()
        if correlation_id == "N/A":
            correlation_id = generate_correlation_id()
            correlation_id_ctx.set(correlation_id)

        try:
            response = await call_next(request)
            request_count += 1
            latency_ms = (time.time() - start_time) * 1000
            log_request(
                logger,
                correlation_id,
                f"{request.method} {request.url.path}",
                latency_ms=latency_ms,
                status=response.status_code,
            )
            return response
        except Exception as e:
            error_count += 1
            logger.error(
                f"Request failed: {e}", extra={"correlation_id": correlation_id}
            )
            raise

    @app.get("/")
    def root() -> dict:
        """Root endpoint."""
        return {
            "status": "ok",
            "message": "Captain Cargo webhook is running.",
            "version": "1.0.0",
        }

    @app.get("/healthz")
    def healthz() -> dict:
        """Liveness check."""
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz() -> dict:
        """Readiness check."""
        dep_status = sanity_client.get_dependency_status()
        return {
            "status": "ready",
            "dependencies": dep_status,
        }

    @app.get("/metrics")
    def metrics() -> dict:
        """Metrics endpoint."""
        return get_metrics()

    @app.post("/webhook")
    async def webhook_handler(request: Request) -> Response:
        """Handle Vapi webhook calls."""
        start_time = time.time()
        correlation_id = correlation_id_ctx.get()

        try:
            body = await request.json()
        except Exception as e:
            logger.error(
                f"Failed to parse webhook body: {e}",
                extra={"correlation_id": correlation_id},
            )
            return JSONResponse(
                content={"status": "error", "message": "Invalid request body"},
                status_code=400,
            )

        try:
            WebhookPayload.model_validate(body)
        except Exception as e:
            logger.warning(
                f"Webhook validation failed: {e}",
                extra={"correlation_id": correlation_id},
            )
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "Validation failed",
                    "details": str(e),
                },
                status_code=422,
            )

        latency_ms = (time.time() - start_time) * 1000
        log_request(logger, correlation_id, "webhook received", latency_ms=latency_ms)

        try:
            response_data = process_webhook(
                body, sanity_client, delivery_cache, response_builder
            )
            latency_ms = (time.time() - start_time) * 1000
            log_request(
                logger, correlation_id, "webhook completed", latency_ms=latency_ms
            )
            return Response(
                content=json.dumps(response_data),
                media_type="application/json",
            )
        except Exception as e:
            logger.error(
                f"Webhook processing failed: {e}",
                extra={"correlation_id": correlation_id},
            )
            return JSONResponse(
                content={"status": "error", "message": "Internal server error"},
                status_code=500,
            )

    def process_webhook(
        body: dict,
        client: SanityClient,
        cache: DeliveryCache,
        builder: ResponseBuilder,
    ) -> dict:
        """Process webhook body and return response."""
        tool_outputs = []

        tool_calls = body.get("message", {}).get("toolCalls", [])

        for call in tool_calls:
            if call.get("type") != "function":
                continue

            tool_call_id = call.get("id")
            if not tool_call_id:
                continue

            func_name = call.get("function", {}).get("name")
            arguments = call.get("function", {}).get("arguments", {})

            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}

            if func_name == "get_delivery_status":
                tracking_id = arguments.get("tracking_id", "")
                try:
                    normalized_id = normalize_tracking_id(tracking_id)
                except ValueError as e:
                    tool_outputs.append(
                        {
                            "toolCallId": tool_call_id,
                            "output": builder.build_error_response(str(e)),
                        }
                    )
                    continue

                cached = cache.get(normalized_id)
                if cached is not None:
                    age_seconds = 0
                    tool_outputs.append(
                        {
                            "toolCallId": tool_call_id,
                            "output": builder.build_cached_fallback(
                                cached, age_seconds
                            ),
                        }
                    )
                    continue

                try:
                    delivery = client.fetch_delivery(normalized_id)
                    if delivery is None:
                        tool_outputs.append(
                            {
                                "toolCallId": tool_call_id,
                                "output": builder.build_not_found_response(
                                    normalized_id
                                ),
                            }
                        )
                    else:
                        response = builder.build_success_response(delivery)
                        cache.set(normalized_id, response.get("delivery_details"))
                        tool_outputs.append(
                            {
                                "toolCallId": tool_call_id,
                                "output": response,
                            }
                        )
                except Exception:
                    fallback = builder.build_unavailable_fallback()
                    tool_outputs.append(
                        {
                            "toolCallId": tool_call_id,
                            "output": fallback,
                        }
                    )

        assistant_messages = []
        for t in tool_outputs:
            if t["output"].get("message"):
                assistant_messages.append(
                    {
                        "role": "assistant",
                        "content": t["output"]["message"],
                    }
                )

        return {
            "toolCallResults": [
                {"toolCallId": t["toolCallId"], "output": t["output"]}
                for t in tool_outputs
            ],
            "messages": assistant_messages,
        }

    return app


def main() -> None:
    """Run the application."""
    config = validate_config()
    app = create_app(config)

    import uvicorn

    def shutdown_handler(signum: Any, frame: Any) -> None:
        """Handle shutdown signals."""
        logger.info("Shutting down gracefully...")
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
