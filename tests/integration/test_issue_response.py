"""Integration tests for issue response formatting."""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from server import create_app
from models.delivery import Delivery, DeliveryStatus
from utils.config import Config


class MockConfig(Config):
    """Mock configuration for testing."""

    def __init__(self) -> None:
        self.SANITY_PROJECT_ID = "test-project"
        self.SANITY_DATASET = "production"
        self.SANITY_API_TOKEN = "test-token"
        self.CACHE_TTL = 60
        self.LOG_LEVEL = "DEBUG"
        self.RATE_LIMIT = 100


class TestIssueResponseIntegration:
    """Integration tests for issue response formatting in webhook."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        config = MockConfig()
        app = create_app(config)
        return TestClient(app)

    def test_webhook_with_empty_tool_calls(self, client: TestClient) -> None:
        """Test webhook handles empty tool calls array."""
        payload = {
            "message": {
                "content": "Hello",
                "toolCalls": [],
            }
        }

        response = client.post("/webhook", json=payload)
        data = response.json()
        assert data["status"] == "error"

    def test_webhook_with_missing_tool_function(self, client: TestClient) -> None:
        """Test webhook handles missing tool function."""
        payload = {
            "message": {
                "content": "Track my package",
                "toolCalls": [
                    {
                        "function": {
                            "name": "unknown_function",
                            "arguments": "{}",
                        }
                    }
                ],
            }
        }

        response = client.post("/webhook", json=payload)
        data = response.json()
        assert data["status"] == "error"

    def test_webhook_with_invalid_arguments(self, client: TestClient) -> None:
        """Test webhook handles invalid tool arguments."""
        payload = {
            "message": {
                "content": "Track package",
                "toolCalls": [
                    {
                        "function": {
                            "name": "track_delivery",
                            "arguments": "invalid json",
                        }
                    }
                ],
            }
        }

        response = client.post("/webhook", json=payload)
        data = response.json()
        assert data["status"] == "error"
