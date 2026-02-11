"""Tests for issue message handling."""

import pytest

from models.delivery import Delivery, DeliveryStatus
from services.response_builder import ResponseBuilder


class TestIssueHandling:
    """Test cases for issue message handling."""

    def test_build_issue_response_with_message(self) -> None:
        """Test building response with issue message."""
        delivery = Delivery(
            tracking_number="TRK123456789",
            status=DeliveryStatus.DELAYED,
            customer_name="John Doe",
            customer_phone="+1234567890",
            estimated_delivery=None,
            issue_message="Package delayed due to weather conditions",
        )

        response = ResponseBuilder.build_issue_response(delivery)

        assert response["status"] == "success"
        assert "weather conditions" in response["message"]
        assert (
            response["delivery_details"]["issue_message"]
            == "Package delayed due to weather conditions"
        )
        assert response["delivery_details"]["tracking_number"] == "TRK123456789"

    def test_build_issue_response_with_empty_message(self) -> None:
        """Test building response with empty issue message."""
        delivery = Delivery(
            tracking_number="TRK123456789",
            status=DeliveryStatus.IN_TRANSIT,
            customer_name="John Doe",
            customer_phone="+1234567890",
            estimated_delivery="2024-01-15T10:00:00Z",
            issue_message="",
        )

        response = ResponseBuilder.build_issue_response(delivery)

        assert response["status"] == "success"
        assert "No issue details available" in response["message"]

    def test_build_issue_response_with_none_message(self) -> None:
        """Test building response with None issue message."""
        delivery = Delivery(
            tracking_number="TRK123456789",
            status=DeliveryStatus.IN_TRANSIT,
            customer_name="John Doe",
            customer_phone="+1234567890",
            estimated_delivery="2024-01-15T10:00:00Z",
            issue_message=None,
        )

        response = ResponseBuilder.build_issue_response(delivery)

        assert response["status"] == "success"
        assert "No issue details available" in response["message"]

    def test_build_no_issue_response(self) -> None:
        """Test building response when no issues exist."""
        response = ResponseBuilder.build_no_issue_response()

        assert response["status"] == "success"
        assert (
            "no recorded issues" in response["message"].lower()
            or "don't see any recorded issues" in response["message"].lower()
        )
        assert response["delivery_details"] is None

    def test_issue_response_preserves_exact_message(self) -> None:
        """Test that issue message is preserved exactly as stored."""
        exact_message = "Customs clearance required - additional documentation needed"
        delivery = Delivery(
            tracking_number="TRK999888777",
            status=DeliveryStatus.DELAYED,
            customer_name="Test User",
            customer_phone="+1111111111",
            estimated_delivery=None,
            issue_message=exact_message,
        )

        response = ResponseBuilder.build_issue_response(delivery)

        assert response["delivery_details"]["issue_message"] == exact_message
        assert exact_message in response["message"]
