"""Statement parsing.

Supports two input formats:

* **CSV** — flexible column detection. Looks for columns matching common bank
  exports (date, description, amount, debit/credit, merchant, currency).
* **PDF** — table extraction with pdfplumber. Falls back to line-by-line
  regex parsing when no tables are detected.

The output is always a list of `ParsedTransaction` dicts that the rest of the
backend can persist without further reshaping.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, asdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
from dateutil import parser as date_parser


# Column header synonyms — lowercase, no spaces, no punctuation.
DATE_KEYS = {"date", "transactiondate", "postingdate", "posted", "valuedate", "operationdate"}
DESC_KEYS = {"description", "details", "narrative", "memo", "transaction", "name", "payee"}
AMOUNT_KEYS = {"amount", "value", "sum"}
DEBIT_KEYS = {"debit", "withdrawal", "out", "spent", "payment"}
CREDIT_KEYS = {"credit", "deposit", "in", "received", "income"}
MERCHANT_KEYS = {"merchant", "counterparty", "vendor"}
CURRENCY_KEYS = {"currency", "ccy"}


@dataclass
class ParsedTransaction:
    occurred_on: date
    description: str
    amount: Decimal
    currency: str = "USD"
    merchant: str | None = None
    raw_source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _match_column(columns: list[str], candidates: set[str]) -> str | None:
    for col in columns:
        if _normalize_key(col) in candidates:
            return col
    return None


def _parse_amount(raw: Any) -> Decimal | None:
    """Parse an amount that may include currency symbols, thousand separators,
    or be wrapped in parentheses (accounting negative).

    Handles both US ("1,234.56") and European ("1.234,56") number formats by
    looking at which separator appears *last*.
    """
    # Pandas turns missing cells into NaN floats; reject them before anything else.
    if raw is None:
        return None
    if isinstance(raw, float) and raw != raw:  # NaN check
        return None
    if isinstance(raw, (int, float, Decimal)):
        try:
            return Decimal(str(raw)).quantize(Decimal("0.01"))
        except InvalidOperation:
            return None

    s = str(raw).strip()
    if not s or s.lower() in {"nan", "none", "-"}:
        return None

    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]

    # Strip currency symbols / letters
    s = re.sub(r"[^\d,.\-+]", "", s)
    if not s:
        return None

    # Determine the decimal separator by position of the last comma vs the last dot.
    last_comma = s.rfind(",")
    last_dot = s.rfind(".")
    if last_comma == -1 and last_dot == -1:
        normalized = s
    elif last_comma > last_dot:
        # "1.234,56" — comma is decimal, dots are thousand separators
        normalized = s.replace(".", "").replace(",", ".")
    else:
        # "1,234.56" — dot is decimal, commas are thousand separators
        normalized = s.replace(",", "")

    try:
        value = Decimal(normalized)
    except InvalidOperation:
        return None
    if negative:
        value = -value
    # Quantize to cents — banks don't track sub-cent amounts and this keeps
    # the API output tidy regardless of whether the source was float or string.
    return value.quantize(Decimal("0.01"))


_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")


def _parse_date(raw: Any) -> date | None:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, date):
        return raw
    s = str(raw).strip()
    if not s:
        return None
    # ISO 8601 (YYYY-MM-DD…) is unambiguous — prefer it over dayfirst heuristics
    # so values like "2026-05-01" parse as May 1, not Jan 5.
    dayfirst = not _ISO_DATE_RE.match(s)
    try:
        return date_parser.parse(s, dayfirst=dayfirst, fuzzy=True).date()
    except (ValueError, TypeError, OverflowError):
        return None


def parse_csv(content: bytes) -> list[ParsedTransaction]:
    """Parse a CSV bank statement.

    Tries a few common delimiters/encodings before giving up.
    """
    last_err: Exception | None = None
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        for sep in (",", ";", "\t", "|"):
            try:
                df = pd.read_csv(
                    io.BytesIO(content),
                    sep=sep,
                    encoding=encoding,
                    engine="python",
                    on_bad_lines="skip",
                )
            except Exception as e:  # noqa: BLE001
                last_err = e
                continue
            if df.shape[1] >= 2 and len(df) > 0:
                return _rows_from_dataframe(df)

    raise ValueError(f"Could not parse CSV: {last_err}")


def _rows_from_dataframe(df: pd.DataFrame) -> list[ParsedTransaction]:
    columns = list(df.columns)
    date_col = _match_column(columns, DATE_KEYS)
    desc_col = _match_column(columns, DESC_KEYS)
    amount_col = _match_column(columns, AMOUNT_KEYS)
    debit_col = _match_column(columns, DEBIT_KEYS)
    credit_col = _match_column(columns, CREDIT_KEYS)
    merchant_col = _match_column(columns, MERCHANT_KEYS)
    currency_col = _match_column(columns, CURRENCY_KEYS)

    if not date_col or not desc_col:
        raise ValueError(
            f"Could not find date/description columns. Got headers: {columns}"
        )
    if not amount_col and not (debit_col or credit_col):
        raise ValueError(
            f"Could not find amount columns. Got headers: {columns}"
        )

    out: list[ParsedTransaction] = []
    for _, row in df.iterrows():
        occurred = _parse_date(row.get(date_col))
        if occurred is None:
            continue

        description = str(row.get(desc_col) or "").strip()
        if not description:
            continue

        if amount_col:
            amount = _parse_amount(row.get(amount_col))
        else:
            debit = _parse_amount(row.get(debit_col)) if debit_col else None
            credit = _parse_amount(row.get(credit_col)) if credit_col else None
            amount = None
            if debit is not None and debit != 0:
                amount = -abs(debit)
            elif credit is not None and credit != 0:
                amount = abs(credit)

        if amount is None or amount == 0:
            continue

        currency = "USD"
        if currency_col:
            cv = str(row.get(currency_col) or "").strip().upper()
            if len(cv) == 3:
                currency = cv

        merchant = None
        if merchant_col:
            mv = str(row.get(merchant_col) or "").strip()
            if mv:
                merchant = mv

        out.append(
            ParsedTransaction(
                occurred_on=occurred,
                description=description,
                amount=amount,
                currency=currency,
                merchant=merchant,
                raw_source=" | ".join(f"{k}={v}" for k, v in row.items() if pd.notna(v))[:500],
            )
        )

    return out


# PDF parsing -----------------------------------------------------------------

_PDF_LINE_RE = re.compile(
    r"""^
    (?P<date>\d{1,2}[./-]\d{1,2}[./-]\d{2,4} | \d{4}-\d{2}-\d{2})
    \s+
    (?P<desc>.+?)
    \s+
    (?P<amount>-?\(?\$?-?[\d,]+\.\d{2}\)?)
    \s*$
    """,
    re.VERBOSE,
)


def parse_pdf(content: bytes) -> list[ParsedTransaction]:
    """Parse a PDF bank statement.

    Strategy: try to extract tables first (most bank statements have them),
    fall back to a line-by-line regex on the raw text.
    """
    # Lazy import so CSV-only deployments don't need pdfplumber.
    import pdfplumber

    transactions: list[ParsedTransaction] = []

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables() or []
            for table in tables:
                if not table or len(table) < 2:
                    continue
                header = [str(c or "").strip() for c in table[0]]
                try:
                    df = pd.DataFrame(table[1:], columns=header)
                    parsed = _rows_from_dataframe(df)
                    transactions.extend(parsed)
                except Exception:
                    continue

            if transactions:
                continue

            text = page.extract_text() or ""
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                m = _PDF_LINE_RE.match(line)
                if not m:
                    continue
                occurred = _parse_date(m.group("date"))
                amount = _parse_amount(m.group("amount"))
                if not occurred or amount is None:
                    continue
                transactions.append(
                    ParsedTransaction(
                        occurred_on=occurred,
                        description=m.group("desc").strip(),
                        amount=amount,
                        raw_source=line[:500],
                    )
                )

    if not transactions:
        raise ValueError("Could not extract any transactions from the PDF.")
    return transactions


def parse_statement(filename: str, content: bytes) -> tuple[str, list[ParsedTransaction]]:
    """Dispatch to the right parser based on filename extension.

    Returns ``(file_type, transactions)``.
    """
    lower = filename.lower()
    if lower.endswith(".csv") or lower.endswith(".tsv"):
        return "csv", parse_csv(content)
    if lower.endswith(".pdf"):
        return "pdf", parse_pdf(content)
    raise ValueError(f"Unsupported file type: {filename}")
