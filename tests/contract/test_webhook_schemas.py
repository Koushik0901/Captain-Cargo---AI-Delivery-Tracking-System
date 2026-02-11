"""Tests for Pydantic webhook schemas."""

import pytest
from pydantic import ValidationError
from models.webhook import ToolCallFunction, ToolCall, VapiMessage, WebhookPayload


class TestWebhookSchemas:
    """Test cases for webhook Pydantic models."""

    def test_tool_call_function_valid(self) -> None:
        """Test valid ToolCallFunction."""
        func = ToolCallFunction(
            name="get_delivery_status", arguments={"tracking_id": "ABC123"}
        )
        assert func.name == "get_delivery_status"
        assert func.arguments == {"tracking_id": "ABC123"}

    def test_tool_call_function_empty_args(self) -> None:
        """Test ToolCallFunction with empty arguments."""
        func = ToolCallFunction(name="test_func")
        assert func.arguments == {}

    def test_tool_call_valid(self) -> None:
        """Test valid ToolCall."""
        tool_call = ToolCall(
            id="call-123",
            type="function",
            function=ToolCallFunction(name="test", arguments={}),
        )
        assert tool_call.id == "call-123"
        assert tool_call.type == "function"

    def test_tool_call_default_type(self) -> None:
        """Test ToolCall default type."""
        tool_call = ToolCall(
            id="call-456",
            function=ToolCallFunction(name="test"),
        )
        assert tool_call.type == "function"

    def test_vapi_message_valid(self) -> None:
        """Test valid VapiMessage."""
        message = VapiMessage(
            type="tool-call",
            tool_calls=[ToolCall(id="call-1", function=ToolCallFunction(name="test"))],
        )
        assert message.type == "tool-call"
        assert len(message.tool_calls) == 1

    def test_vapi_message_empty_tool_calls(self) -> None:
        """Test VapiMessage with empty tool calls list."""
        message = VapiMessage(tool_calls=[])
        assert message.tool_calls == []

    def test_webhook_payload_valid(self) -> None:
        """Test valid WebhookPayload."""
        payload = WebhookPayload(
            message=VapiMessage(
                type="tool-call",
                tool_calls=[
                    ToolCall(
                        id="call-1",
                        function=ToolCallFunction(name="get_delivery_status"),
                    )
                ],
            )
        )
        assert payload.message.type == "tool-call"
        assert len(payload.message.tool_calls) == 1

    def test_webhook_payload_empty_tool_calls_rejected(self) -> None:
        """Test that empty tool calls list is rejected."""
        with pytest.raises(ValidationError) as excinfo:
            WebhookPayload(message=VapiMessage(tool_calls=[]))
        assert "At least one tool call is required" in str(excinfo.value)

    def test_webhook_payload_minimal(self) -> None:
        """Test minimal valid webhook payload."""
        payload = WebhookPayload(
            message=VapiMessage(
                tool_calls=[
                    ToolCall(id="minimal", function=ToolCallFunction(name="test"))
                ]
            )
        )
        assert payload.message.type == "tool-call"
