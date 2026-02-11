"""Delivery entity models."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DeliveryStatus(str, Enum):
    """Status of a delivery."""

    PROCESSING = "processing"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    DELAYED = "delayed"


class Delivery(BaseModel):
    """Core delivery entity from Sanity CMS."""

    tracking_number: str = Field(
        ..., alias="trackingNumber", min_length=6, max_length=32
    )
    status: DeliveryStatus
    customer_name: str = Field(..., alias="customerName")
    customer_phone: str = Field(..., alias="customerPhone")
    estimated_delivery: Optional[str] = Field(None, alias="estimatedDelivery")
    issue_message: Optional[str] = Field(None, alias="issueMessage")

    class Config:
        populate_by_name = True


class DeliveryResponse(BaseModel):
    """Response format for delivery data."""

    tracking_number: str
    status: DeliveryStatus
    customer_name: str
    estimated_delivery: Optional[str]
    issue_message: Optional[str]
