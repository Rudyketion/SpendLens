"""Analytics over the transactions table."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from .categorizer import CATEGORIES


_CAT_LOOKUP = {c.name: c for c in CATEGORIES}


def _date_range(db: Session, start: date | None, end: date | None) -> tuple[date | None, date | None]:
    return start, end


def _apply_range(query, start: date | None, end: date | None):
    if start is not None:
        query = query.where(models.Transaction.occurred_on >= start)
    if end is not None:
        query = query.where(models.Transaction.occurred_on <= end)
    return query


def totals(db: Session, start: date | None = None, end: date | None = None) -> schemas.TotalsOut:
    q = select(models.Transaction)
    q = _apply_range(q, start, end)
    rows = db.execute(q).scalars().all()

    income = Decimal(0)
    expense = Decimal(0)
    for r in rows:
        if r.amount > 0:
            income += r.amount
        else:
            expense += r.amount  # negative
    return schemas.TotalsOut(
        income=income,
        expense=expense,
        net=income + expense,
        transaction_count=len(rows),
    )


def category_breakdown(
    db: Session, start: date | None = None, end: date | None = None
) -> list[schemas.CategoryBreakdownItem]:
    """Spending share per category. Income/Transfers are excluded from the
    denominator so the percentages reflect *spending* shares."""
    q = select(models.Transaction).join(models.Category, isouter=True)
    q = _apply_range(q, start, end)
    rows = db.execute(q).scalars().all()

    totals_by_cat: dict[str, Decimal] = defaultdict(Decimal)
    counts: Counter[str] = Counter()
    expense_total = Decimal(0)

    for r in rows:
        cat_name = r.category.name if r.category else "Other"
        if r.amount < 0 and cat_name not in {"Income", "Transfers"}:
            amt = abs(r.amount)
            totals_by_cat[cat_name] += amt
            counts[cat_name] += 1
            expense_total += amt

    items: list[schemas.CategoryBreakdownItem] = []
    for name, total in sorted(totals_by_cat.items(), key=lambda kv: kv[1], reverse=True):
        cdef = _CAT_LOOKUP.get(name, _CAT_LOOKUP["Other"])
        share = float(total / expense_total) if expense_total > 0 else 0.0
        items.append(
            schemas.CategoryBreakdownItem(
                category=name,
                color=cdef.color,
                icon=cdef.icon,
                total=total,
                share=share,
                transaction_count=counts[name],
            )
        )
    return items


def timeseries(
    db: Session,
    bucket: str = "day",
    start: date | None = None,
    end: date | None = None,
) -> list[schemas.TimeseriesPoint]:
    if bucket not in {"day", "month"}:
        raise ValueError("bucket must be 'day' or 'month'")

    q = select(models.Transaction)
    q = _apply_range(q, start, end)
    rows = db.execute(q).scalars().all()

    buckets: dict[str, tuple[Decimal, Decimal]] = {}
    for r in rows:
        if bucket == "day":
            key = r.occurred_on.isoformat()
        else:
            key = r.occurred_on.replace(day=1).isoformat()

        inc, exp = buckets.get(key, (Decimal(0), Decimal(0)))
        if r.amount > 0:
            inc += r.amount
        else:
            exp += -r.amount
        buckets[key] = (inc, exp)

    points = [
        schemas.TimeseriesPoint(bucket=k, income=v[0], expense=v[1])
        for k, v in sorted(buckets.items())
    ]
    return points


def insights(db: Session, start: date | None = None, end: date | None = None) -> list[schemas.InsightOut]:
    """Generate a handful of natural-language insights.

    Deterministic and cheap — no LLM call. Good enough to demo "an app that
    understands your spending" without burning tokens on every reload.
    """
    out: list[schemas.InsightOut] = []
    q = select(models.Transaction)
    q = _apply_range(q, start, end)
    rows = db.execute(q).scalars().all()
    if not rows:
        return out

    # 1) Top merchant by spend
    merchant_totals: dict[str, Decimal] = defaultdict(Decimal)
    for r in rows:
        if r.amount < 0:
            key = (r.merchant or r.description).split("  ")[0][:48]
            merchant_totals[key] += -r.amount
    if merchant_totals:
        top_merchant, top_amount = max(merchant_totals.items(), key=lambda kv: kv[1])
        out.append(
            schemas.InsightOut(
                kind="top_merchant",
                title="Where you spent the most",
                body=f"You spent the most at **{top_merchant}**.",
                value=f"${top_amount:,.2f}",
            )
        )

    # 2) Savings rate
    income = sum((r.amount for r in rows if r.amount > 0), Decimal(0))
    expense = sum((-r.amount for r in rows if r.amount < 0), Decimal(0))
    if income > 0:
        rate = float((income - expense) / income)
        nice = f"{rate * 100:.1f}%"
        if rate >= 0.2:
            body = "Solid — you're keeping more than 20% of what comes in."
        elif rate >= 0:
            body = "You're net positive, but there's room to push savings higher."
        else:
            body = "You're spending more than you earn this period."
        out.append(
            schemas.InsightOut(
                kind="savings_rate",
                title="Savings rate",
                body=body,
                value=nice,
            )
        )

    # 3) Likely subscriptions — same merchant within ~30 days at similar amount.
    subs: Counter[tuple[str, Decimal]] = Counter()
    for r in rows:
        if r.amount >= 0:
            continue
        key = ((r.merchant or r.description).split("  ")[0][:40].strip(), abs(r.amount))
        subs[key] += 1
    recurring = [(m, amt, n) for (m, amt), n in subs.items() if n >= 2]
    if recurring:
        recurring.sort(key=lambda x: x[2], reverse=True)
        m, amt, n = recurring[0]
        out.append(
            schemas.InsightOut(
                kind="subscriptions",
                title="Possible recurring charge",
                body=f"**{m}** charged you ~${amt:,.2f} on {n} occasions. Check if it's still worth it.",
                value=f"{n}× ${amt:,.2f}",
            )
        )

    # 4) Biggest single expense
    biggest = min((r for r in rows if r.amount < 0), key=lambda r: r.amount, default=None)
    if biggest:
        out.append(
            schemas.InsightOut(
                kind="biggest_jump",
                title="Biggest single expense",
                body=f"**{biggest.description[:60]}** on {biggest.occurred_on.isoformat()}.",
                value=f"${abs(biggest.amount):,.2f}",
            )
        )

    return out
