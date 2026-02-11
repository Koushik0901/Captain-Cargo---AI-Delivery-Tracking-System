"""Integration tests for webhook endpoint."""

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


class TestWebhookEndpoint:
    """Integration tests for /webhook endpoint."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        config = MockConfig()
        app = create_app(config)
        return TestClient(app)

    def test_root_endpoint(self, client: TestClient) -> None:
        """Test root endpoint returns welcome message."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "Captain Cargo" in data["message"]

    def test_health_endpoint(self, client: TestClient) -> None:
        """Test health endpoint returns ok."""
        response = client.get("/healthz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_ready_endpoint(self, client: TestClient) -> None:
        """Test ready endpoint returns dependency status."""
        response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_metrics_endpoint(self, client: TestClient) -> None:
        """Test metrics endpoint returns metrics."""
        response = client.get("/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "requests_total" in data

    def test_webhook_with_empty_body(self, client: TestClient) -> None:
        """Test webhook handles empty body gracefully."""
        response = client.post("/webhook", json={})

        assert response.status_code in [400, 422]
        data = response.json()
        assert data["status"] == "error"

    def test_webhook_with_invalid_json(self, client: TestClient) -> None:
        """Test webhook handles invalid JSON gracefully."""
        response = client.post(
            "/webhook",
            content="not valid json",
            headers={"content-type": "application/json"},
        )

        assert response.status_code == 400
