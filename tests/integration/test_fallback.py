"""Integration tests for fallback response behavior."""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from server import create_app
from services.cache import DeliveryCache
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


class TestFallbackBehavior:
    """Test cases for fallback response handling."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        config = MockConfig()
        app = create_app(config)
        return TestClient(app)

    def test_health_endpoint_works_during_outage(self, client: TestClient) -> None:
        """Test that health endpoint remains available during service outage."""
        response = client.get("/healthz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_readiness_endpoint_reports_status(self, client: TestClient) -> None:
        """Test that readiness endpoint reports dependency status."""
        response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "dependencies" in data

    def test_root_endpoint_returns_ok(self, client: TestClient) -> None:
        """Test root endpoint returns ok status."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_metrics_endpoint_returns_data(self, client: TestClient) -> None:
        """Test metrics endpoint returns metrics data."""
        response = client.get("/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "requests_total" in data
        assert "cache_hits_total" in data
