"""Seed the database with realistic demo transactions.

Run with:

    python -m app.seed

Useful for screenshots and for running the frontend without uploading a file first.
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from . import models
from .database import SessionLocal, init_db
from .services.categorizer import CATEGORIES, rule_based_category


MERCHANTS_BY_CATEGORY: dict[str, list[tuple[str, float, float]]] = {
    # name, min, max
    "Groceries":    [("Whole Foods Market", 30, 120), ("Trader Joe's", 20, 90), ("Costco Wholesale", 50, 220)],
    "Restaurants":  [("Starbucks #4421", 4, 12), ("Chipotle 0188", 9, 18), ("DoorDash", 18, 55), ("Sushi Yama", 25, 70)],
    "Transport":    [("Uber Trip", 6, 35), ("Shell Gas Station", 30, 80), ("Lyft Ride", 8, 28)],
    "Housing":      [("Apartment Rent", 1600, 1600)],
    "Utilities":    [("Comcast Internet", 75, 75), ("ConEd Electric", 60, 140), ("T-Mobile Postpaid", 50, 50)],
    "Subscriptions":[("Netflix", 15.49, 15.49), ("Spotify Premium", 11.99, 11.99), ("Anthropic API", 20, 20), ("GitHub", 4, 4)],
    "Shopping":     [("Amazon.com", 15, 250), ("Nike Store", 60, 180), ("IKEA", 40, 350)],
    "Health":       [("CVS Pharmacy", 8, 60), ("Dental Clinic", 80, 250)],
    "Entertainment":[("AMC Theatres", 14, 40), ("Steam Games", 20, 60)],
    "Travel":       [("Delta Airlines", 180, 520), ("Airbnb", 90, 280)],
    "Fees":         [("ATM Fee", 3, 3), ("Overdraft Fee", 35, 35)],
}


def seed(months: int = 3) -> None:
    init_db()
    random.seed(42)

    with SessionLocal() as db:
        # Categories
        existing = {c.name: c for c in db.execute(select(models.Category)).scalars()}
        for cdef in CATEGORIES:
            if cdef.name not in existing:
                cat = models.Category(name=cdef.name, color=cdef.color, icon=cdef.icon)
                db.add(cat)
                existing[cdef.name] = cat
        db.flush()

        # Skip if already seeded
        already = db.execute(select(models.Transaction).limit(1)).scalar()
        if already:
            print("Database already has transactions — skipping seed.")
            return

        today = date.today()
        start = today - timedelta(days=30 * months)

        statement = models.Statement(
            filename="seed-demo-data",
            file_type="csv",
            row_count=0,
        )
        db.add(statement)
        db.flush()

        count = 0
        cur = start
        while cur <= today:
            # Monthly recurrent
            if cur.day == 1:
                for cat_name in ("Housing", "Subscriptions", "Utilities"):
                    for merchant, lo, hi in MERCHANTS_BY_CATEGORY[cat_name]:
                        amount = Decimal(f"{random.uniform(lo, hi):.2f}")
                        _add_tx(db, statement.id, existing, cur, merchant, -amount, cat_name)
                        count += 1
                # Monthly salary
                _add_tx(db, statement.id, existing, cur, "ACH Payroll Deposit", Decimal("4200.00"), "Income")
                count += 1

            # 1-4 random transactions per day
            for _ in range(random.randint(1, 4)):
                cat_name = random.choices(
                    population=["Groceries", "Restaurants", "Transport", "Shopping", "Health",
                                "Entertainment", "Travel", "Fees"],
                    weights=[18, 25, 14, 12, 5, 8, 4, 2],
                    k=1,
                )[0]
                merchant, lo, hi = random.choice(MERCHANTS_BY_CATEGORY[cat_name])
                amount = Decimal(f"{random.uniform(lo, hi):.2f}")
                _add_tx(db, statement.id, existing, cur, merchant, -amount, cat_name)
                count += 1

            cur += timedelta(days=1)

        statement.row_count = count
        db.commit()
        print(f"Seeded {count} transactions across {months} months.")


def _add_tx(
    db,
    statement_id: int,
    categories: dict,
    occurred_on: date,
    description: str,
    amount: Decimal,
    cat_name: str,
) -> None:
    # Use the rule-based categorizer as a sanity check — but always prefer
    # the explicit category we picked.
    _ = rule_based_category(description, float(amount))
    db.add(
        models.Transaction(
            occurred_on=occurred_on,
            description=description,
            merchant=description.split("  ")[0][:64],
            amount=amount,
            currency="USD",
            category_id=categories[cat_name].id,
            statement_id=statement_id,
        )
    )


if __name__ == "__main__":
    seed()
