"""
Pydantic schemas for Payment System.

This module provides type-safe request/response models for payment processing,
including Razorpay integration, webhook handling, and retry mechanisms.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, ConfigDict
from enum import Enum

from app.schemas.common import BaseResponse, PaginatedResponse, PaymentStatusEnum


# Payment Order Schemas

class PaymentOrderCreateRequest(BaseModel):
    """Request model for creating payment orders"""
    order_id: str = Field(..., description="Associated order ID")
    amount: int = Field(..., gt=0, description="Payment amount in paise (INR)")
    currency: str = Field("INR", description="Payment currency")
    notes: Optional[Dict[str, Any]] = Field(None, description="Additional payment metadata")

class PaymentOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for payment orders"""
    id: int
    order_id: str
    user_id: str
    razorpay_order_id: str
    amount: int
    currency: str
    status: str
    payment_link: Optional[str]
    payment_link_id: Optional[str]
    expires_at: datetime
    retry_count: int
    max_retry_attempts: int
    notes: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

class PaymentTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for payment transactions"""
    id: int
    payment_order_id: int
    user_id: str
    razorpay_payment_id: str
    amount: int
    currency: str
    status: str
    method: Optional[str]
    captured: bool
    fee: Optional[int]
    tax: Optional[int]
    error_code: Optional[str]
    error_description: Optional[str]
    notes: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

class WebhookEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for webhook events"""
    id: int
    event_id: str
    event: str
    entity: str
    account_id: str
    payload: Dict[str, Any]
    processed: bool
    created_at: datetime
    processed_at: Optional[datetime]

class PaymentRetryAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for payment retry attempts"""
    id: int
    payment_order_id: int
    attempt_number: int
    razorpay_order_id: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime

class PaymentOrderSearchRequest(BaseModel):
    """Request model for searching payment orders"""
    user_id: Optional[str] = Field(None, description="Filter by user")
    status: Optional[PaymentStatusEnum] = Field(None, description="Filter by status")
    amount_min: Optional[int] = Field(None, description="Minimum amount filter")
    amount_max: Optional[int] = Field(None, description="Maximum amount filter")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order")


# List Response Models

class PaymentOrderListResponse(PaginatedResponse):
    """Paginated response for payment orders"""
    items: List[PaymentOrderResponse]


class PaymentTransactionListResponse(PaginatedResponse):
    """Paginated response for payment transactions"""
    items: List[PaymentTransactionResponse]


class WebhookEventListResponse(PaginatedResponse):
    """Paginated response for webhook events"""
    items: List[WebhookEventResponse]


# Action Response Models

class PaymentOrderCreateResponse(BaseResponse):
    """Response for payment order creation"""
    payment_order: PaymentOrderResponse
    payment_link: Optional[str]


class PaymentStatusUpdateResponse(BaseResponse):
    """Response for payment status updates"""
    payment_order: PaymentOrderResponse
    transaction: Optional[PaymentTransactionResponse]


class WebhookProcessResponse(BaseResponse):
    """Response for webhook processing"""
    event: WebhookEventResponse
    actions_taken: List[str]


# Analytics Schemas

class PaymentAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for payment analytics"""
    total_payments: int
    successful_payments: int
    failed_payments: int
    pending_payments: int
    success_rate: float
    total_amount: int
    average_amount: int

    # Breakdown
    payments_by_status: Dict[str, int]
    payments_by_method: Dict[str, int]
    revenue_trend: List[Dict[str, Any]]

    # Period
    period_start: datetime
    period_end: datetime
