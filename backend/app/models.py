"""SQLAlchemy ORM models."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


from .database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    color: Mapped[str] = mapped_column(String(16), default="#94a3b8")
    icon: Mapped[str] = mapped_column(String(32), default="circle")

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    occurred_on: Mapped[date] = mapped_column(Date, index=True)
    description: Mapped[str] = mapped_column(Text)
    # Positive = income, negative = expense. Stored as Decimal to avoid float drift.
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    merchant: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_source: Mapped[str | None] = mapped_column(Text, nullable=True)

    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    category: Mapped[Category | None] = relationship(back_populates="transactions")

    statement_id: Mapped[int | None] = mapped_column(
        ForeignKey("statements.id", ondelete="SET NULL"), nullable=True, index=True
    )
    statement: Mapped["Statement | None"] = relationship(back_populates="transactions")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_tx_date_amount", "occurred_on", "amount"),
    )


class Statement(Base):
    """Represents an uploaded bank statement (CSV or PDF)."""

    __tablename__ = "statements"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(16))  # csv | pdf
    row_count: Mapped[int] = mapped_column(default=0)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    transactions: Mapped[list[Transaction]] = relationship(back_populates="statement")
