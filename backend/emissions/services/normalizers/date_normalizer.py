"""
Date Normalizer
===============
Enterprise data comes with wildly inconsistent date formats:
  - SAP:     "20231015" (YYYYMMDD compact)
  - Utility: "Oct-2023" (billing month)
  - Travel:  "15/10/2023" or "10/15/2023" (ambiguous!)
  - German:  "15.10.2023"

We use python-dateutil for intelligent parsing with explicit
dayfirst/yearfirst hints per source system.
"""

from datetime import date, datetime
from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta
import re


def normalize_date(raw_date: str, source_hint: str = 'AUTO') -> date:
    """
    Parses a raw date string into a Python date object.

    Args:
        raw_date:    The date string as found in the source file.
        source_hint: 'SAP', 'UTILITY', 'TRAVEL', or 'AUTO'

    Returns:
        datetime.date

    Raises:
        ValueError if parsing fails completely.
    """
    raw = str(raw_date).strip()

    # ── SAP compact format YYYYMMDD ────────────────────────────────────────────
    if source_hint == 'SAP' or re.fullmatch(r'\d{8}', raw):
        try:
            return datetime.strptime(raw, '%Y%m%d').date()
        except ValueError:
            pass

    # ── German/European dot-separated: DD.MM.YYYY ──────────────────────────────
    if re.fullmatch(r'\d{1,2}\.\d{1,2}\.\d{4}', raw):
        return datetime.strptime(raw, '%d.%m.%Y').date()

    # ── Utility billing month: Oct-2023 / 2023-10 / October 2023 ──────────────
    if source_hint == 'UTILITY':
        # "Oct-2023" or "October 2023" → use last day of that month
        try:
            parsed = dateutil_parser.parse(raw, dayfirst=False)
            # Billing data represents the END of a billing period
            return (parsed.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)).date()
        except (ValueError, OverflowError):
            pass

    # ── ISO 8601 fallback ──────────────────────────────────────────────────────
    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y']:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue

    # ── Last resort: dateutil with dayfirst=True (European default) ────────────
    try:
        return dateutil_parser.parse(raw, dayfirst=True).date()
    except (ValueError, OverflowError):
        raise ValueError(f"Cannot parse date: '{raw_date}'. "
                         f"Tried SAP compact, German, ISO 8601, and dateutil fallback.")