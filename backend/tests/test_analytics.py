"""Tests for the analytics service.

We build a tiny in-memory SQLite DB, populate it with hand-picked transactions,
and assert that totals/breakdown/timeseries/insights produce the right numbers.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.database import Base
from app.services import analytics
from app.services.categorizer import CATEGORIES


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)
    session = SessionLocal()

    # Categories
    cats: dict[str, models.Category] = {}
    for cdef in CATEGORIES:
        cat = models.Category(name=cdef.name, color=cdef.color, icon=cdef.icon)
        session.add(cat)
        cats[cdef.name] = cat
    session.flush()

    # Transactions
    rows = [
        ("Groceries", "Whole Foods", date(2026, 5, 1), Decimal("-50.00")),
        ("Groceries", "Whole Foods", date(2026, 5, 8), Decimal("-30.00")),
        ("Restaurants", "Starbucks", date(2026, 5, 1), Decimal("-5.00")),
        ("Restaurants", "Starbucks", date(2026, 5, 2), Decimal("-5.00")),
        ("Subscriptions", "Netflix", date(2026, 5, 1), Decimal("-15.49")),
        ("Subscriptions", "Netflix", date(2026, 6, 1), Decimal("-15.49")),
        ("Income", "Payroll", date(2026, 5, 1), Decimal("4000.00")),
        ("Transfers", "Savings transfer", date(2026, 5, 5), Decimal("-200.00")),
    ]
    for cat_name, desc, day, amount in rows:
        session.add(
            models.Transaction(
                occurred_on=day,
                description=desc,
                merchant=desc,
                amount=amount,
                currency="USD",
                category_id=cats[cat_name].id,
            )
        )
    session.commit()
    yield session
    session.close()


def test_totals(db):
    t = analytics.totals(db)
    assert t.income == Decimal("4000.00")
    # All negative amounts including transfers
    assert t.expense == Decimal("-320.98")
    assert t.net == Decimal("3679.02")
    assert t.transaction_count == 8


def test_category_breakdown_excludes_income_and_transfers(db):
    items = analytics.category_breakdown(db)
    names = [i.category for i in items]
    assert "Income" not in names
    assert "Transfers" not in names
    # Groceries should be the biggest spend bucket here (80 > 30.98 subs > 10 dining)
    assert items[0].category == "Groceries"
    assert items[0].total == Decimal("80.00")
    # Shares must sum to ~1
    assert abs(sum(i.share for i in items) - 1.0) < 1e-6


def test_timeseries_day_bucket(db):
    points = analytics.timeseries(db, bucket="day")
    by_bucket = {p.bucket: p for p in points}
    assert "2026-05-01" in by_bucket
    # On 5/1: income 4000, expense 50 (groceries) + 5 (starbucks) + 15.49 (netflix) = 70.49
    p = by_bucket["2026-05-01"]
    assert p.income == Decimal("4000.00")
    assert p.expense == Decimal("70.49")


def test_timeseries_month_bucket(db):
    points = analytics.timeseries(db, bucket="month")
    buckets = [p.bucket for p in points]
    assert "2026-05-01" in buckets
    assert "2026-06-01" in buckets


def test_timeseries_rejects_invalid_bucket(db):
    with pytest.raises(ValueError):
        analytics.timeseries(db, bucket="quarter")


def test_insights_finds_recurring_charge(db):
    insights = {i.kind: i for i in analytics.insights(db)}
    # Netflix charged twice with identical amount → counts as recurring
    assert "subscriptions" in insights
    assert "Netflix" in insights["subscriptions"].body


def test_insights_savings_rate(db):
    insights = {i.kind: i for i in analytics.insights(db)}
    assert "savings_rate" in insights
    assert "%" in insights["savings_rate"].value


def test_insights_top_merchant_is_highest_outflow(db):
    insights = {i.kind: i for i in analytics.insights(db)}
    assert "top_merchant" in insights
    # Savings transfer (200) > Whole Foods (80) > Netflix (30.98) > Starbucks (10)
    assert "Savings transfer" in insights["top_merchant"].body
