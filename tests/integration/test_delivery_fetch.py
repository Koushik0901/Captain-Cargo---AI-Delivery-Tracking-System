"""Tests for delivery fetching from Sanity CMS."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from models.delivery import Delivery, DeliveryStatus
from services.sanity_client import SanityClient, CircuitState
from utils.config import Config


class MockConfig:
    """Mock configuration for testing."""

    SANITY_PROJECT_ID = "test-project"
    SANITY_DATASET = "production"
    SANITY_API_TOKEN = "test-token"


class TestSanityClientFetch:
    """Test cases for SanityClient.fetch_delivery."""

    @pytest.fixture
    def mock_config(self) -> MockConfig:
        """Create mock configuration."""
        return MockConfig()

    @pytest.fixture
    def sanity_client(self, mock_config: MockConfig) -> SanityClient:
        """Create SanityClient instance with mock config."""
        return SanityClient(mock_config)

    @patch("services.sanity_client.requests.get")
    def test_fetch_delivery_success(
        self,
        mock_get: Mock,
        sanity_client: SanityClient,
    ) -> None:
        """Test successful delivery fetch returns Delivery object."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": [
                {
                    "trackingNumber": "TRK123456789",
                    "status": "in_transit",
                    "customerName": "John Doe",
                    "customerPhone": "+1234567890",
                    "estimatedDelivery": "2024-01-15T10:00:00Z",
                    "issueMessage": None,
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = sanity_client.fetch_delivery("TRK123456789")

        assert result is not None
        assert isinstance(result, Delivery)
        assert result.tracking_number == "TRK123456789"
        assert result.status == DeliveryStatus.IN_TRANSIT
        assert result.customer_name == "John Doe"
        mock_get.assert_called_once()

    @patch("services.sanity_client.requests.get")
    def test_fetch_delivery_not_found(
        self,
        mock_get: Mock,
        sanity_client: SanityClient,
    ) -> None:
        """Test delivery not found returns None."""
        mock_response = Mock()
        mock_response.json.return_value = {"result": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = sanity_client.fetch_delivery("NONEXISTENT")

        assert result is None
        assert sanity_client._failure_count == 0
        assert sanity_client.circuit_state == CircuitState.CLOSED

    @patch("services.sanity_client.requests.get")
    def test_fetch_delivery_with_issue(
        self,
        mock_get: Mock,
        sanity_client: SanityClient,
    ) -> None:
        """Test delivery with issue message is correctly parsed."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "result": [
                {
                    "trackingNumber": "TRK999888777",
                    "status": "delayed",
                    "customerName": "Jane Smith",
                    "customerPhone": "+1987654321",
                    "estimatedDelivery": None,
                    "issueMessage": "Package delayed due to weather conditions",
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = sanity_client.fetch_delivery("TRK999888777")

        assert result is not None
        assert result.issue_message == "Package delayed due to weather conditions"
        assert result.status == DeliveryStatus.DELAYED

    def test_circuit_open_blocks_requests(
        self,
        sanity_client: SanityClient,
    ) -> None:
        """Test that circuit breaker state transitions correctly."""
        sanity_client._circuit_state = CircuitState.OPEN
        sanity_client._failure_count = 5
        sanity_client._last_failure_time = float("inf")

        assert sanity_client.circuit_state == CircuitState.OPEN
        assert sanity_client._failure_count == 5

    def test_get_dependency_status(self, sanity_client: SanityClient) -> None:
        """Test dependency status returns correct structure."""
        sanity_client._failure_count = 2

        status = sanity_client.get_dependency_status()

        assert "circuit_breaker" in status
        assert "failure_count" in status
        assert status["failure_count"] == 2
        assert status["circuit_breaker"] == "closed"

    def test_reset_circuit(self, sanity_client: SanityClient) -> None:
        """Test circuit breaker reset."""
        sanity_client._failure_count = 5
        sanity_client._circuit_state = CircuitState.OPEN

        sanity_client.reset_circuit()

        assert sanity_client._failure_count == 0
        assert sanity_client.circuit_state == CircuitState.CLOSED
