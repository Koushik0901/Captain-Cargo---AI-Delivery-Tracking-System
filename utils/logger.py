"""Structured JSON logging utilities."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", "N/A"),
            "latency_ms": getattr(record, "latency_ms", None),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logger(name: str = "voice_agent") -> logging.Logger:
    """Set up structured JSON logger.

    Args:
        name: Logger name.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    return logger


def log_request(
    logger_instance: logging.Logger,
    correlation_id: str,
    event: str,
    latency_ms: float | None = None,
    status: int | None = None,
    **kwargs: Any,
) -> None:
    """Log a request event with structured data.

    Args:
        logger_instance: Logger instance to use.
        correlation_id: Unique correlation ID for the request.
        event: Event description.
        latency_ms: Request latency in milliseconds.
        status: HTTP status code.
        **kwargs: Additional fields to include in log.
    """
    extra: dict[str, Any] = {"correlation_id": correlation_id, "latency_ms": latency_ms}
    if status is not None:
        extra["status"] = status
    logger_instance.info(event, extra=extra)


logger = setup_logger()
