"""Environment configuration validation."""

import os
from typing import Any


class Config:
    """Configuration loaded from environment variables."""

    SANITY_PROJECT_ID: str
    SANITY_DATASET: str
    SANITY_API_TOKEN: str
    CACHE_TTL: int = 60
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT: int = 100

    def __init__(self, **kwargs: Any) -> None:
        """Initialize config from environment or kwargs."""
        self.SANITY_PROJECT_ID = self._get_required("SANITY_PROJECT_ID", kwargs)
        self.SANITY_DATASET = self._get_required("SANITY_DATASET", kwargs)
        self.SANITY_API_TOKEN = self._get_required("SANITY_API_TOKEN", kwargs)
        self.CACHE_TTL = int(kwargs.get("CACHE_TTL", os.getenv("CACHE_TTL", "60")))
        self.LOG_LEVEL = kwargs.get("LOG_LEVEL", os.getenv("LOG_LEVEL", "INFO"))
        self.RATE_LIMIT = int(kwargs.get("RATE_LIMIT", os.getenv("RATE_LIMIT", "100")))

    def _get_required(self, key: str, kwargs: dict[str, Any]) -> str:
        """Get required environment variable."""
        value = kwargs.get(key) or os.getenv(key)
        if not value:
            raise ValueError(
                f"Required environment variable '{key}' is not set. "
                f"Please set it in your .env file or environment."
            )
        return value


def validate_config() -> Config:
    """Validate that all required environment variables are present.

    Returns:
        Validated Config instance.

    Raises:
        ValueError: If any required variable is missing.
    """
    return Config()
