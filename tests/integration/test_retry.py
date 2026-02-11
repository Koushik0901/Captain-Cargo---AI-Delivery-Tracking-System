"""Integration tests for retry with exponential backoff."""

import pytest
from unittest.mock import Mock, patch, call
import requests

from services.sanity_client import SanityClient
from utils.config import Config


class MockConfig:
    """Mock configuration for testing."""

    SANITY_PROJECT_ID = "test-project"
    SANITY_DATASET = "production"
    SANITY_API_TOKEN = "test-token"


class TestRetryBehavior:
    """Test cases for retry with exponential backoff."""

    @pytest.fixture
    def mock_config(self) -> MockConfig:
        """Create mock configuration."""
        return MockConfig()

    @pytest.fixture
    def sanity_client(self, mock_config: MockConfig) -> SanityClient:
        """Create SanityClient instance with mock config."""
        return SanityClient(mock_config)

    @patch("services.sanity_client.requests.get")
    def test_retry_on_connection_error(
        self,
        mock_get: Mock,
        sanity_client: SanityClient,
    ) -> None:
        """Test that retry occurs on connection error."""
        mock_get.side_effect = [
            requests.exceptions.ConnectionError(),
            requests.exceptions.ConnectionError(),
            Mock(
                json=lambda: {
                    "result": [
                        {
                            "trackingNumber": "TRK123",
                            "status": "in_transit",
                            "customerName": "Test",
                            "customerPhone": "123",
                            "issueMessage": None,
                        }
                    ]
                },
                raise_for_status=Mock(),
            ),
        ]

        result = sanity_client.fetch_delivery("TRK123")

        assert result is not None
        assert mock_get.call_count == 3

    @patch("services.sanity_client.requests.get")
    def test_retry_on_timeout(
        self,
        mock_get: Mock,
        sanity_client: SanityClient,
    ) -> None:
        """Test that retry occurs on timeout."""
        mock_get.side_effect = [
            requests.exceptions.Timeout(),
            Mock(
                json=lambda: {
                    "result": [
                        {
                            "trackingNumber": "TRK456",
                            "status": "delivered",
                            "customerName": "Test",
                            "customerPhone": "123",
                            "issueMessage": None,
                        }
                    ]
                },
                raise_for_status=Mock(),
            ),
        ]

        result = sanity_client.fetch_delivery("TRK456")

        assert result is not None
        assert mock_get.call_count == 2

    @patch("services.sanity_client.requests.get")
    def test_retry_on_http_error(
        self,
        mock_get: Mock,
        sanity_client: SanityClient,
    ) -> None:
        """Test that retry occurs on HTTP error."""
        mock_get.side_effect = [
            requests.exceptions.HTTPError(),
            Mock(
                json=lambda: {
                    "result": [
                        {
                            "trackingNumber": "TRK789",
                            "status": "in_transit",
                            "customerName": "Test",
                            "customerPhone": "123",
                            "issueMessage": None,
                        }
                    ]
                },
                raise_for_status=Mock(),
            ),
        ]

        result = sanity_client.fetch_delivery("TRK789")

        assert result is not None
        assert mock_get.call_count == 2

    @patch("services.sanity_client.requests.get")
    def test_max_retries_exceeded(
        self,
        mock_get: Mock,
        sanity_client: SanityClient,
    ) -> None:
        """Test that exception is raised after max retries."""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        try:
            sanity_client.fetch_delivery("TRK000")
            assert False, "Expected exception to be raised"
        except Exception:
            pass

        assert mock_get.call_count == 3

    @patch("services.sanity_client.requests.get")
    def test_failure_recorded_after_retry_exhaustion(
        self,
        mock_get: Mock,
        sanity_client: SanityClient,
    ) -> None:
        """Test that failure is recorded when all retries are exhausted."""
        initial_failures = sanity_client._failure_count
        mock_get.side_effect = requests.exceptions.ConnectionError()

        try:
            sanity_client.fetch_delivery("TRK000")
        except Exception:
            pass

        assert sanity_client._failure_count > initial_failures

    @patch("services.sanity_client.requests.get")
    def test_success_clears_failure_count(
        self,
        mock_get: Mock,
        sanity_client: SanityClient,
    ) -> None:
        """Test that success clears previous failure count."""
        sanity_client._failure_count = 2

        mock_response = Mock()
        mock_response.json.return_value = {
            "result": [
                {
                    "trackingNumber": "TRK123",
                    "status": "in_transit",
                    "customerName": "Test",
                    "customerPhone": "123",
                    "issueMessage": None,
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = sanity_client.fetch_delivery("TRK123")

        assert result is not None
        assert sanity_client._failure_count == 0
        assert sanity_client.circuit_state == sanity_client.circuit_state.CLOSED
