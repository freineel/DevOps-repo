from __future__ import annotations

import logging
import threading
from datetime import date
from typing import Any, Protocol

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
    """Used by the tests and when no DATABASE_URL is set.

    Data is lost when the process exits.
    """

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


# Arbitrary constant: every worker asks Postgres for the same lock number.
_SCHEMA_LOCK_ID = 4_242_001


def _row_to_expense(row: tuple[Any, ...]) -> Expense:
    expense_id, amount_cents, category, spent_on = row
    # The column is DATE, so psycopg returns datetime.date. The API (and the
    # month filter in routes.py) works with "YYYY-MM-DD" strings.
    return Expense(
        id=expense_id,
        amount_cents=amount_cents,
        category=category,
        spent_on=spent_on.isoformat(),
    )


class PostgresExpenseRepository:
    """Postgres backend, used when DATABASE_URL is set (docker compose)."""

    # Fixed constant inserted via f-string (never user input); values always
    # go through %s placeholders.
    _COLUMNS = "id, amount_cents, category, spent_on"

    def __init__(self, dsn: str) -> None:
        # Imported here, not at module level: tests and local runs without a
        # database never load the driver.
        from psycopg_pool import ConnectionPool

        # A pool reuses open connections instead of opening one per request
        # (a new Postgres connection costs a few milliseconds and a process).
        self._pool = ConnectionPool(dsn, min_size=1, max_size=5, open=True)
        self._create_schema()

    def _create_schema(self) -> None:
        with self._pool.connection() as conn:
            # With 2 gunicorn workers, both run this at the same moment.
            # Parallel CREATE TABLE IF NOT EXISTS can still collide inside
            # Postgres, so the advisory lock lets only one worker in at a time.
            # The lock is released automatically at the end of the transaction.
            conn.execute("SELECT pg_advisory_xact_lock(%s)", (_SCHEMA_LOCK_ID,))
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS expenses (
                    id           SERIAL PRIMARY KEY,
                    -- BIGINT: INTEGER would cap at about 21 million francs.
                    amount_cents BIGINT NOT NULL CHECK (amount_cents > 0),
                    category     TEXT   NOT NULL,
                    -- DATE instead of TEXT: Postgres rejects invalid dates
                    -- and can sort and filter by date natively.
                    spent_on     DATE   NOT NULL
                )
                """
            )
        # Leaving the "with" block commits the transaction.

    def list(self) -> list[Expense]:
        with self._pool.connection() as conn:
            rows = conn.execute(f"SELECT {self._COLUMNS} FROM expenses ORDER BY id").fetchall()
        return [_row_to_expense(row) for row in rows]

    def get(self, expense_id: int) -> Expense | None:
        # %s is a placeholder: psycopg sends the value separately from the SQL
        # text, so user input can never change the query (no SQL injection).
        with self._pool.connection() as conn:
            row = conn.execute(
                f"SELECT {self._COLUMNS} FROM expenses WHERE id = %s", (expense_id,)
            ).fetchone()
        return _row_to_expense(row) if row else None

    def add(self, amount_cents: int, category: str, spent_on: str) -> Expense:
        # RETURNING gives back the row incl. the id Postgres generated, so no
        # second SELECT is needed.
        with self._pool.connection() as conn:
            row = conn.execute(
                "INSERT INTO expenses (amount_cents, category, spent_on) "
                f"VALUES (%s, %s, %s) RETURNING {self._COLUMNS}",
                (amount_cents, category, date.fromisoformat(spent_on)),
            ).fetchone()
        return _row_to_expense(row)

    def delete(self, expense_id: int) -> bool:
        with self._pool.connection() as conn:
            result = conn.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
        return result.rowcount > 0

    def healthy(self) -> bool:
        # Backs /ready: if the database is gone, the app reports "not ready"
        # instead of failing on every request.
        try:
            # Short timeout: the pool would otherwise wait 30 s for a
            # connection, and the readiness probe would hang that long.
            with self._pool.connection(timeout=2) as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            log.exception("database health check failed")
            return False


def create_repository(config: Config) -> ExpenseRepository:
    if config.database_url:
        log.info("using postgres repository")
        return PostgresExpenseRepository(config.database_url)
    # Each gunicorn worker imports the app separately, so the in-memory store
    # is NOT shared between workers. Set DATABASE_URL to get a shared store.
    log.warning(
        "no DATABASE_URL set, using in-memory repository: "
        "state is per-process and is lost on restart"
    )
    return InMemoryExpenseRepository()
