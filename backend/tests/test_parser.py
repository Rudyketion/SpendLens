"""Tests for the CSV parser and rule-based categorizer.

These tests pin the contract of the parsing pipeline. The categorizer tests
intentionally use the rule-based path so they don't require a network call
or an Anthropic API key.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.services.categorizer import CATEGORY_NAMES, rule_based_category
from app.services.parser import parse_csv, _parse_amount, _parse_date


CSV_SAMPLE = b"""Date,Description,Amount
2026-05-01,Starbucks #4421,-5.75
2026-05-02,ACH Payroll Deposit,4200.00
2026-05-03,Uber Trip,-14.20
2026-05-04,Whole Foods Market,-62.30
"""


def test_parse_csv_basic():
    rows = parse_csv(CSV_SAMPLE)
    assert len(rows) == 4
    assert rows[0].description == "Starbucks #4421"
    assert rows[0].amount == Decimal("-5.75")
    assert rows[1].amount == Decimal("4200.00")
    assert rows[0].occurred_on == date(2026, 5, 1)


def test_parse_csv_iso_dates_not_dayfirst():
    """Regression: '2026-05-01' must parse as May 1, not Jan 5."""
    rows = parse_csv(b"Date,Description,Amount\n2026-05-01,Test,-10.00\n")
    assert rows[0].occurred_on == date(2026, 5, 1)


def test_parse_csv_european_format():
    csv = (
        "Date;Description;Amount\n"
        "01.05.2026;Lidl;-45,30\n"
        "02.05.2026;Salary;3.200,00\n"
    ).encode()
    rows = parse_csv(csv)
    assert [r.amount for r in rows] == [Decimal("-45.30"), Decimal("3200.00")]
    assert rows[0].occurred_on == date(2026, 5, 1)


def test_parse_csv_debit_credit_columns():
    csv = b"""Posting Date,Narrative,Debit,Credit
2026-05-01,Coffee Bean,4.50,
2026-05-02,Refund,,12.00
"""
    rows = parse_csv(csv)
    assert len(rows) == 2
    assert rows[0].amount == Decimal("-4.50")
    assert rows[1].amount == Decimal("12.00")


def test_parse_csv_dayfirst_when_ambiguous():
    rows = parse_csv(b"Date,Description,Amount\n15/03/2026,Test,-10.00\n")
    assert rows[0].occurred_on == date(2026, 3, 15)


def test_parse_csv_us_thousands_and_parens():
    csv = b"""Date,Description,Amount
2026-05-01,Vendor,(123.45)
2026-05-02,Big Bonus,"$1,234.56"
"""
    rows = parse_csv(csv)
    assert rows[0].amount == Decimal("-123.45")
    assert rows[1].amount == Decimal("1234.56")


def test_parse_csv_missing_columns_raises():
    # No description column -> should fail loudly
    with pytest.raises(ValueError):
        parse_csv(b"Date,Amount\n2026-05-01,-10.00\n")


@pytest.mark.parametrize("raw", [None, float("nan"), "", "nan", "-", "  "])
def test_parse_amount_invalid_inputs(raw):
    assert _parse_amount(raw) is None


def test_parse_date_handles_iso_and_eu():
    assert _parse_date("2026-05-01") == date(2026, 5, 1)
    assert _parse_date("01.05.2026") == date(2026, 5, 1)
    assert _parse_date("invalid") is None


def test_rule_based_categories():
    assert rule_based_category("Starbucks #4421", -5.75) == "Restaurants"
    assert rule_based_category("ACH Payroll Deposit", 4200.0) == "Income"
    assert rule_based_category("Uber Trip", -14.2) == "Transport"
    assert rule_based_category("Whole Foods Market", -62.3) == "Groceries"
    assert rule_based_category("Mystery Merchant", -10.0) == "Other"


def test_rule_based_returns_only_known_categories():
    """Whatever the input, the classifier never invents a new label."""
    for desc, amt in [("xyz", -1), ("abc", 1), ("Netflix", -15.49), ("Atm fee", -3)]:
        assert rule_based_category(desc, amt) in CATEGORY_NAMES


def test_rule_based_income_keyword_with_negative_amount_falls_back():
    """A negative-amount 'refund' shouldn't get classified as Income."""
    cat = rule_based_category("Refund Amazon.com", -18.99)
    assert cat != "Income"
