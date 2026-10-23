from __future__ import annotations

from dataclasses import asdict, dataclass
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


# TODO (you): validation functions, one per field, each raising ValidationError
# with a clear message. Compare with validate_title() in the Taskboard app.
#   validate_amount_cents(raw) -> int   positive int, no bool (bool is an int!)
#   validate_category(raw)     -> str   non-empty after strip()
#   validate_spent_on(raw)     -> str   valid ISO date, date.fromisoformat helps
