"""Tests for response builder."""

import pytest
from models.delivery import Delivery, DeliveryStatus
from services.response_builder import ResponseBuilder


class TestResponseBuilder:
    """Test cases for ResponseBuilder."""

    @pytest.fixture
    def sample_delivery(self) -> Delivery:
        """Create a sample delivery."""
        return Delivery(
            tracking_number="ABC123",
            status=DeliveryStatus.IN_TRANSIT,
            customer_name="John Doe",
            customer_phone="555-1234",
            estimated_delivery="2024-01-15",
            issue_message=None,
        )

    @pytest.fixture
    def delivery_with_issue(self) -> Delivery:
        """Create a delivery with issue."""
        return Delivery(
            tracking_number="XYZ789",
            status=DeliveryStatus.DELAYED,
            customer_name="Jane Smith",
            customer_phone="555-5678",
            estimated_delivery=None,
            issue_message="Package delayed due to weather",
        )

    def test_build_success_response(self, sample_delivery: Delivery) -> None:
        """Test building success response."""
        response = ResponseBuilder.build_success_response(sample_delivery)

        assert response["status"] == "success"
        assert "ABC123" in response["message"]
        assert "in transit" in response["message"]
        assert response["delivery_details"]["tracking_number"] == "ABC123"
        assert response["delivery_details"]["status"] == "in_transit"

    def test_build_not_found_response(self) -> None:
        """Test building not-found response."""
        response = ResponseBuilder.build_not_found_response("UNKNOWN123")

        assert response["status"] == "not_found"
        assert "UNKNOWN123" in response["message"]
        assert response["delivery_details"] is None

    def test_build_error_response(self) -> None:
        """Test building error response."""
        response = ResponseBuilder.build_error_response("Something went wrong")

        assert response["status"] == "error"
        assert response["message"] == "Something went wrong"
        assert response["delivery_details"] is None

    def test_build_issue_response(self, delivery_with_issue: Delivery) -> None:
        """Test building issue response."""
        response = ResponseBuilder.build_issue_response(delivery_with_issue)

        assert response["status"] == "success"
        assert "weather" in response["message"]
        assert (
            response["delivery_details"]["issue_message"]
            == "Package delayed due to weather"
        )

    def test_build_no_issue_response(self) -> None:
        """Test building no-issue response."""
        response = ResponseBuilder.build_no_issue_response()

        assert response["status"] == "success"
        assert "recorded issues" in response["message"]
        assert response["delivery_details"] is None

    def test_build_cached_fallback(self) -> None:
        """Test building cached fallback response."""
        cached_data = {"status": "in_transit"}
        response = ResponseBuilder.build_cached_fallback(cached_data, age_seconds=30)

        assert response["status"] == "success"
        assert "30 seconds ago" in response["message"]
        assert response["source"] == "cache"
        assert response["cache_age_seconds"] == 30
        assert response["delivery_details"] == cached_data

    def test_build_unavailable_fallback(self) -> None:
        """Test building unavailable fallback response."""
        response = ResponseBuilder.build_unavailable_fallback()

        assert response["status"] == "unavailable"
        assert "trouble accessing" in response["message"]
        assert response["source"] == "fallback"
        assert response["delivery_details"] is None
