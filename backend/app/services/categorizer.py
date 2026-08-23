"""Transaction categorization.

Two modes:

1. **AI mode** (default when `ANTHROPIC_API_KEY` is set). Sends a batch of
   transaction descriptions to Claude and asks for a category per row.
2. **Rule-based fallback** — a deterministic keyword classifier so the app
   still works offline and during tests.

Both modes return categories from the same fixed taxonomy, which is also
used to seed the database.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from ..config import get_settings

log = logging.getLogger(__name__)


# Fixed taxonomy. Order matters: first match wins in the rule-based fallback.
@dataclass(frozen=True)
class CategoryDef:
    name: str
    color: str
    icon: str
    keywords: tuple[str, ...]


CATEGORIES: tuple[CategoryDef, ...] = (
    CategoryDef("Groceries", "#22c55e", "shopping-cart",
                ("grocer", "supermarket", "whole foods", "trader joe", "kroger", "tesco", "lidl",
                 "aldi", "atb", "walmart", "safeway", "publix", "costco")),
    CategoryDef("Restaurants", "#f97316", "utensils",
                ("restaurant", "cafe", "coffee", "starbucks", "mcdonald", "kfc", "subway",
                 "pizza", "burger", "chipotle", "doordash", "ubereats", "grubhub", "deliveroo")),
    CategoryDef("Transport", "#3b82f6", "car",
                ("uber", "lyft", "bolt", "taxi", "metro", "subway pass", "transit", "gas",
                 "shell", "chevron", "bp ", "exxon", "parking", "toll")),
    CategoryDef("Housing", "#a855f7", "home",
                ("rent", "mortgage", "landlord", "lease", "hoa")),
    CategoryDef("Utilities", "#0ea5e9", "zap",
                ("electric", "water bill", "gas bill", "internet", "comcast", "verizon",
                 "t-mobile", "att ", "spectrum")),
    CategoryDef("Subscriptions", "#ec4899", "repeat",
                ("netflix", "spotify", "hulu", "disney", "apple", "icloud", "youtube premium",
                 "github", "openai", "anthropic", "adobe", "notion", "figma", "dropbox")),
    CategoryDef("Shopping", "#eab308", "shopping-bag",
                ("amazon", "ebay", "etsy", "nike", "adidas", "zara", "h&m", "ikea", "target")),
    CategoryDef("Health", "#ef4444", "heart-pulse",
                ("pharmacy", "cvs", "walgreens", "clinic", "hospital", "doctor", "dental",
                 "optical")),
    CategoryDef("Entertainment", "#8b5cf6", "film",
                ("cinema", "movie", "theatre", "theater", "steam", "playstation", "xbox",
                 "concert", "ticketmaster")),
    CategoryDef("Travel", "#06b6d4", "plane",
                ("airline", "airbnb", "booking", "hotel", "expedia", "kayak", "delta",
                 "united", "lufthansa", "ryanair", "easyjet")),
    CategoryDef("Income", "#10b981", "trending-up",
                ("salary", "payroll", "deposit", "refund", "interest", "dividend", "stripe",
                 "paypal received", "venmo received")),
    CategoryDef("Transfers", "#64748b", "arrow-right-left",
                ("transfer", "savings", "wire", "zelle", "venmo", "paypal")),
    CategoryDef("Fees", "#dc2626", "receipt",
                ("fee", "atm", "overdraft", "service charge", "interest charged")),
    CategoryDef("Other", "#94a3b8", "circle", ()),
)

CATEGORY_NAMES: tuple[str, ...] = tuple(c.name for c in CATEGORIES)


def rule_based_category(description: str, amount: float | None = None) -> str:
    """Pick a category from CATEGORIES based on keywords in the description."""
    d = description.lower()
    for cat in CATEGORIES:
        for kw in cat.keywords:
            if kw in d:
                # Income keywords on a negative amount usually mean a refund-like outflow:
                # treat as Other rather than misclassify.
                if cat.name == "Income" and amount is not None and amount < 0:
                    continue
                return cat.name
    # Default: positive amount → Income, otherwise Other.
    if amount is not None and amount > 0:
        return "Income"
    return "Other"


def categorize_batch(
    items: list[tuple[str, float]],
    *,
    use_ai: bool | None = None,
) -> list[str]:
    """Categorize a batch of (description, amount) tuples.

    Returns a list of category names of the same length as ``items``.
    Always falls back to rule-based classification if the AI call fails.
    """
    if not items:
        return []

    settings = get_settings()
    if use_ai is None:
        use_ai = settings.ai_enabled

    rule_fallback = [rule_based_category(d, a) for d, a in items]

    if not use_ai:
        return rule_fallback

    try:
        return _categorize_with_claude(items, model=settings.anthropic_model)
    except Exception as e:  # noqa: BLE001
        log.warning("AI categorization failed (%s) — falling back to rules", e)
        return rule_fallback


def _categorize_with_claude(items: list[tuple[str, float]], model: str) -> list[str]:
    """Ask Claude to classify each transaction. Robust to JSON drift."""
    # Lazy import so the app still starts without the anthropic library installed.
    import anthropic

    client = anthropic.Anthropic()

    rows = [{"i": i, "desc": d, "amount": float(a)} for i, (d, a) in enumerate(items)]
    categories_list = ", ".join(CATEGORY_NAMES)

    system = (
        "You are a precise personal-finance transaction categorizer. "
        "For each transaction, return exactly one category from this fixed list: "
        f"{categories_list}. "
        "Positive amounts are inflows (income/refund/transfer-in), "
        "negative amounts are outflows. "
        "Respond with ONLY a JSON array of objects: "
        '[{"i": <int>, "category": "<one of the categories>"}, ...] '
        "in the same order as the input. No prose."
    )
    user = json.dumps(rows, ensure_ascii=False)

    resp = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")

    parsed = _extract_json_array(text)
    by_index: dict[int, str] = {}
    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        idx = entry.get("i")
        cat = entry.get("category")
        if isinstance(idx, int) and isinstance(cat, str) and cat in CATEGORY_NAMES:
            by_index[idx] = cat

    return [by_index.get(i, rule_based_category(d, a)) for i, (d, a) in enumerate(items)]


_JSON_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)


def _extract_json_array(text: str) -> list:
    text = text.strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        pass
    m = _JSON_ARRAY_RE.search(text)
    if m:
        try:
            data = json.loads(m.group(0))
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []
    return []
