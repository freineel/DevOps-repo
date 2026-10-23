from __future__ import annotations

import logging
import threading
from typing import Protocol

from app.config import Config
from app.models import Expense

log = logging.getLogger(__name__)


class ExpenseRepository(Protocol):
    """Storage contract. Routes depend on this, never on a concrete backend.

    Filtering and aggregation happen in the routes on top of list(), so a
    second backend (Postgres, week 4) only has to implement these methods.
    """

    def list(self) -> list[Expense]: ...
    def get(self, expense_id: int) -> Expense | None: ...
    def add(self, amount_cents: int, category: str, spent_on: str) -> Expense: ...
    def delete(self, expense_id: int) -> bool: ...
    def healthy(self) -> bool: ...


class InMemoryExpenseRepository:
    """Default backend until week 4. Data is lost when the process exits."""

    def __init__(self) -> None:
        self._expenses: dict[int, Expense] = {}
        self._next_id = 1
        # Flask's dev server and gunicorn threads may serve requests in
        # parallel; the lock keeps id assignment consistent.
        self._lock = threading.Lock()

    def list(self) -> list[Expense]:
        with self._lock:
            return sorted(self._expenses.values(), key=lambda e: e.id)

    def get(self, expense_id: int) -> Expense | None:
        with self._lock:
            return self._expenses.get(expense_id)

    def add(self, amount_cents: int, category: str, spent_on: str) -> Expense:
        with self._lock:
            expense = Expense(
                id=self._next_id,
                amount_cents=amount_cents,
                category=category,
                spent_on=spent_on,
            )
            self._expenses[expense.id] = expense
            self._next_id += 1
            return expense

    def delete(self, expense_id: int) -> bool:
        with self._lock:
            return self._expenses.pop(expense_id, None) is not None

    def healthy(self) -> bool:
        return True


def create_repository(config: Config) -> ExpenseRepository:
    if config.database_url:
        # Postgres backend follows in week 4; until then fail loudly instead of
        # silently ignoring a configured database.
        raise NotImplementedError("Postgres repository is added in week 4")
    log.warning(
        "no DATABASE_URL set, using in-memory repository: "
        "state is per-process and is lost on restart"
    )
    return InMemoryExpenseRepository()
