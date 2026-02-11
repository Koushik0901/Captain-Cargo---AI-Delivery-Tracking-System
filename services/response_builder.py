"""Response builder for hallucination-safe responses."""

from typing import Optional

from models.delivery import Delivery, DeliveryResponse


class ResponseBuilder:
    """Builds responses from verified tool outputs only."""

    @staticmethod
    def build_success_response(delivery: Delivery) -> dict:
        """Build success response from verified delivery data.

        Args:
            delivery: Verified Delivery object.

        Returns:
            Structured response dict.
        """
        return {
            "status": "success",
            "message": f"Your package {delivery.tracking_number} is {delivery.status.value.replace('_', ' ')}.",
            "delivery_details": {
                "tracking_number": delivery.tracking_number,
                "status": delivery.status.value,
                "customer_name": delivery.customer_name,
                "estimated_delivery": delivery.estimated_delivery,
                "issue_message": delivery.issue_message,
            },
        }

    @staticmethod
    def build_not_found_response(tracking_id: str) -> dict:
        """Build not-found response.

        Args:
            tracking_id: The tracking ID that wasn't found.

        Returns:
            Structured response dict.
        """
        return {
            "status": "not_found",
            "message": f"I couldn't find a delivery with tracking number {tracking_id}. Please verify your tracking number and try again.",
            "delivery_details": None,
        }

    @staticmethod
    def build_error_response(message: str) -> dict:
        """Build error response.

        Args:
            message: Error message.

        Returns:
            Structured response dict.
        """
        return {
            "status": "error",
            "message": message,
            "delivery_details": None,
        }

    @staticmethod
    def build_issue_response(delivery: Delivery) -> dict:
        """Build response for issue-related queries.

        Args:
            delivery: Verified Delivery object with issue.

        Returns:
            Structured response dict.
        """
        issue_text = delivery.issue_message or "No issue details available."
        return {
            "status": "success",
            "message": f"I see there's an issue: {issue_text}",
            "delivery_details": {
                "tracking_number": delivery.tracking_number,
                "status": delivery.status.value,
                "issue_message": issue_text,
            },
        }

    @staticmethod
    def build_no_issue_response() -> dict:
        """Build response when no issues exist.

        Returns:
            Structured response dict.
        """
        return {
            "status": "success",
            "message": "I don't see any recorded issues for this delivery.",
            "delivery_details": None,
        }

    @staticmethod
    def build_cached_fallback(cached_data: dict, age_seconds: int) -> dict:
        """Build fallback response using cached data.

        Args:
            cached_data: Cached delivery data.
            age_seconds: How old the cached data is.

        Returns:
            Structured response dict with freshness indicator.
        """
        return {
            "status": "success",
            "message": f"I have cached information from {age_seconds} seconds ago. For the latest status, please try again later.",
            "delivery_details": cached_data,
            "source": "cache",
            "cache_age_seconds": age_seconds,
        }

    @staticmethod
    def build_unavailable_fallback() -> dict:
        """Build fallback response when data is unavailable.

        Returns:
            Structured response dict.
        """
        return {
            "status": "unavailable",
            "message": "I'm having trouble accessing the latest delivery information. Please try again in a moment.",
            "delivery_details": None,
            "source": "fallback",
        }
