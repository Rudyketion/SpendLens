"""Pydantic schemas — the API contract."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str
    icon: str


class TransactionBase(BaseModel):
    occurred_on: date
    description: str
    amount: Decimal
    currency: str = "USD"
    merchant: str | None = None


class TransactionCreate(TransactionBase):
    category_id: int | None = None


class TransactionUpdate(BaseModel):
    description: str | None = None
    amount: Decimal | None = None
    merchant: str | None = None
    category_id: int | None = None


class TransactionOut(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: CategoryOut | None = None
    created_at: datetime


class StatementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_type: str
    row_count: int
    uploaded_at: datetime


class UploadResult(BaseModel):
    statement: StatementOut
    imported: int
    categorized: int
    skipped: int = 0


# ----- Analytics -----


class TotalsOut(BaseModel):
    income: Decimal
    expense: Decimal
    net: Decimal
    transaction_count: int


class CategoryBreakdownItem(BaseModel):
    category: str
    color: str
    icon: str
    total: Decimal
    share: float = Field(..., description="Share of total expense, 0..1")
    transaction_count: int


class TimeseriesPoint(BaseModel):
    bucket: str  # ISO date (day or month start)
    income: Decimal
    expense: Decimal


class InsightOut(BaseModel):
    kind: str  # "top_merchant" | "biggest_jump" | "savings_rate" | "subscriptions"
    title: str
    body: str
    value: str | None = None
