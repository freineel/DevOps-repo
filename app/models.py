from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any


@dataclass
class Expense:
    id: int
    # Stored in cents (Rappen) as an integer: floats cannot represent 0.10
    # exactly, so summing float amounts drifts (0.1 + 0.2 != 0.3).
    amount_cents: int
    category: str
    # ISO date "YYYY-MM-DD". A plain string keeps JSON trivial, and the month
    # filter becomes a prefix check ("2026-10").
    spent_on: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ValidationError(ValueError):
    """Raised when client input does not satisfy the Expense invariants."""


# Validation runs before anything reaches the repository, so the repository can
# trust its input. Every function returns the cleaned value or raises
# ValidationError; routes.py turns that into a 400 response.


def validate_amount_cents(raw: Any) -> int:
    # bool is a subclass of int in Python, so without the explicit check
    # {"amount_cents": true} would be accepted as 1 cent.
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise ValidationError("amount_cents must be an integer (cents)")
    if raw <= 0:
        raise ValidationError("amount_cents must be greater than 0")
    return raw


def validate_category(raw: Any) -> str:
    if not isinstance(raw, str):
        raise ValidationError("category must be a string")
    category = raw.strip()
    if not category:
        raise ValidationError("category must not be empty")
    return category


def validate_spent_on(raw: Any) -> str:
    if not isinstance(raw, str):
        raise ValidationError("spent_on must be a date string YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(raw)
    except ValueError:
        # "from None" hides the internal ValueError; the client only needs our message.
        raise ValidationError("spent_on must be a valid date YYYY-MM-DD") from None
    # Normalise to YYYY-MM-DD so the month filter (prefix check) always works.
    return parsed.isoformat()


_MONTH_PATTERN = re.compile(r"\d{4}-(0[1-9]|1[0-2])")


def validate_month(raw: Any) -> str:
    """Query filter ?month=YYYY-MM."""
    if not isinstance(raw, str) or not _MONTH_PATTERN.fullmatch(raw):
        raise ValidationError("month must have the format YYYY-MM")
    return raw
