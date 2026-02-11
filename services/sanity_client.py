"""Sanity CMS client with retry and circuit breaker."""

import time
from enum import Enum
from typing import Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from models.delivery import Delivery, DeliveryStatus
from utils.config import Config


class CircuitState(str, Enum):
    """Circuit breaker state."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class SanityClient:
    """Client for fetching delivery data from Sanity CMS."""

    def __init__(self, config: Config) -> None:
        """Initialize client.

        Args:
            config: Configuration object.
        """
        self.config = config
        self.base_url = f"https://{config.SANITY_PROJECT_ID}.api.sanity.io/v2021-10-21/data/query/{config.SANITY_DATASET}"
        self._circuit_state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._failure_threshold = 5
        self._reset_timeout = 30.0

    @property
    def circuit_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        if self._circuit_state == CircuitState.OPEN:
            if time.time() - self._last_failure_time > self._reset_timeout:
                self._circuit_state = CircuitState.HALF_OPEN
        return self._circuit_state

    def _record_failure(self) -> None:
        """Record a failure for circuit breaker."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self._failure_threshold:
            self._circuit_state = CircuitState.OPEN

    def _record_success(self) -> None:
        """Record a success for circuit breaker."""
        self._failure_count = 0
        self._circuit_state = CircuitState.CLOSED

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, min=0.1, max=0.4),
    )
    def fetch_delivery(self, tracking_number: str) -> Optional[Delivery]:
        """Fetch delivery from Sanity CMS.

        Args:
            tracking_number: Normalized tracking number.

        Returns:
            Delivery object or None if not found.
        """
        if self.circuit_state == CircuitState.OPEN:
            raise Exception("Circuit breaker is open - service unavailable")

        query = f"*[_type == 'delivery' && trackingNumber == $tracking_number]{{trackingNumber,status,customerName,customerPhone,estimatedDelivery,issueMessage}}"
        params = {"tracking_number": tracking_number}

        start_time = time.time()
        try:
            response = requests.get(
                self.base_url,
                params={"query": query},
                headers={"Authorization": f"Bearer {self.config.SANITY_API_TOKEN}"},
                timeout=5.0,
            )
            response.raise_for_status()
            data = response.json()

            latency_ms = (time.time() - start_time) * 1000

            result = data.get("result", [])
            if not result:
                self._record_success()
                return None

            delivery_data = result[0]
            delivery = Delivery(
                tracking_number=delivery_data["trackingNumber"],
                status=DeliveryStatus(delivery_data["status"]),
                customer_name=delivery_data["customerName"],
                customer_phone=delivery_data["customerPhone"],
                estimated_delivery=delivery_data.get("estimatedDelivery"),
                issue_message=delivery_data.get("issueMessage"),
            )

            self._record_success()
            return delivery

        except Exception:
            self._record_failure()
            raise

    def get_dependency_status(self) -> dict:
        """Get dependency status for health checks.

        Returns:
            Status dict with circuit breaker state and failure count.
        """
        return {
            "circuit_breaker": self.circuit_state.value,
            "failure_count": self._failure_count,
        }

    def reset_circuit(self) -> None:
        """Manually reset the circuit breaker."""
        self._failure_count = 0
        self._circuit_state = CircuitState.CLOSED
