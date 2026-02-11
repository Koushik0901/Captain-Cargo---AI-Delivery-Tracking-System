"""Tests for metrics endpoint."""

import pytest
from fastapi.testclient import TestClient

from server import create_app
from endpoints.metrics import get_metrics
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


class TestMetricsEndpoint:
    """Test cases for metrics endpoint."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        config = MockConfig()
        app = create_app(config)
        return TestClient(app)

    def test_metrics_returns_json(self, client: TestClient) -> None:
        """Test /metrics endpoint returns JSON."""
        response = client.get("/metrics")

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_metrics_contains_required_fields(self, client: TestClient) -> None:
        """Test /metrics endpoint contains all required metric fields."""
        response = client.get("/metrics")

        assert response.status_code == 200
        data = response.json()
        required_fields = [
            "requests_total",
            "errors_total",
            "cache_hits_total",
            "cache_misses_total",
            "cache_size",
            "cache_hit_rate",
        ]
        for field in required_fields:
            assert field in data

    def test_metrics_types(self, client: TestClient) -> None:
        """Test /metrics endpoint returns correct types."""
        response = client.get("/metrics")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["requests_total"], int)
        assert isinstance(data["errors_total"], int)
        assert isinstance(data["cache_hits_total"], int)
        assert isinstance(data["cache_misses_total"], int)
        assert isinstance(data["cache_size"], int)
        assert isinstance(data["cache_hit_rate"], float)

    def test_metrics_values_are_non_negative(self, client: TestClient) -> None:
        """Test /metrics endpoint returns non-negative values."""
        response = client.get("/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["requests_total"] >= 0
        assert data["errors_total"] >= 0
        assert data["cache_hits_total"] >= 0
        assert data["cache_misses_total"] >= 0
        assert data["cache_size"] >= 0
        assert data["cache_hit_rate"] >= 0.0

    def test_get_metrics_function(self) -> None:
        """Test get_metrics function returns correct structure."""
        metrics = get_metrics()

        required_fields = [
            "requests_total",
            "errors_total",
            "cache_hits_total",
            "cache_misses_total",
            "cache_size",
            "cache_hit_rate",
        ]
        for field in required_fields:
            assert field in metrics

    def test_cache_hit_rate_calculation(self) -> None:
        """Test cache hit rate is calculated correctly."""
        metrics = get_metrics()

        hits = metrics["cache_hits_total"]
        misses = metrics["cache_misses_total"]
        total = hits + misses
        expected_rate = hits / total if total > 0 else 0.0

        assert abs(metrics["cache_hit_rate"] - expected_rate) < 0.001
