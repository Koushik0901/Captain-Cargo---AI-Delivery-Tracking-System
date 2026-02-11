"""Pydantic models for Vapi webhook payloads."""

from pydantic import BaseModel, Field, model_validator
from typing import Optional


class ToolCallFunction(BaseModel):
    """Function call details from Vapi webhook."""

    name: str = Field(..., description="Name of the function to call")
    arguments: dict = Field(
        default_factory=dict, description="Arguments for the function"
    )


class ToolCall(BaseModel):
    """Individual tool call from Vapi."""

    id: str = Field(..., description="Unique identifier for this tool call")
    type: str = Field(default="function", description="Type of tool call")
    function: ToolCallFunction = Field(..., description="Function details")


class VapiMessage(BaseModel):
    """Message payload from Vapi webhook."""

    type: str = Field(default="tool-call", description="Message type")
    tool_calls: list[ToolCall] = Field(
        default_factory=list, description="List of tool calls"
    )


class WebhookPayload(BaseModel):
    """Root webhook payload from Vapi."""

    message: VapiMessage = Field(..., description="Vapi message payload")

    @model_validator(mode="after")
    def validate_tool_calls(self) -> "WebhookPayload":
        """Ensure we have at least one tool call."""
        if not self.message.tool_calls:
            raise ValueError("At least one tool call is required")
        return self
