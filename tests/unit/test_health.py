"""Tests for health check endpoints."""

import pytest
from fastapi.testclient import TestClient

from server import create_app


class TestHealthEndpoints:
    """Test cases for health check endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create test client."""
        app = create_app()
        return TestClient(app)

    def test_healthz_returns_ok(self, client: TestClient) -> None:
        """Test /healthz endpoint returns ok status."""
        response = client.get("/healthz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_healthz_content_type(self, client: TestClient) -> None:
        """Test /healthz endpoint returns JSON content type."""
        response = client.get("/healthz")

        assert response.headers["content-type"] == "application/json"

    def test_readyz_returns_ready(self, client: TestClient) -> None:
        """Test /readyz endpoint returns ready status."""
        response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_readyz_includes_dependencies(self, client: TestClient) -> None:
        """Test /readyz endpoint includes dependencies dict."""
        response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()
        assert "dependencies" in data
        assert isinstance(data["dependencies"], dict)

    def test_health_response_model(self, client: TestClient) -> None:
        """Test /healthz response matches expected model."""
        response = client.get("/healthz")

        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"status"}

    def test_readiness_response_model(self, client: TestClient) -> None:
        """Test /readyz response matches expected model."""
        response = client.get("/readyz")

        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"status", "dependencies"}
