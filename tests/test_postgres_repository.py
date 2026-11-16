"""Tests for PostgresExpenseRepository against a real Postgres database.

These tests need a running Postgres. They read the connection string from the
environment variable TEST_DATABASE_URL:

- In the CI pipeline, a Postgres service container runs next to the tests and
  TEST_DATABASE_URL is set, so these tests run.
- Locally, TEST_DATABASE_URL is usually not set, so these tests are skipped.

Why TEST_DATABASE_URL and not DATABASE_URL? The tests delete all rows before
each test. A separate variable makes sure they never empty a real database by
accident.
"""

import os

import psycopg
import pytest

from app.config import Config
from app.repository import PostgresExpenseRepository, create_repository

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

# Skip every test in this file when no test database is configured.
pytestmark = pytest.mark.skipif(
    TEST_DATABASE_URL is None,
    reason="TEST_DATABASE_URL is not set, no Postgres available",
)


def delete_all_expenses():
    """Empty the table and reset the id counter, so every test starts at id 1."""
    connection = psycopg.connect(TEST_DATABASE_URL)
    connection.execute("TRUNCATE expenses RESTART IDENTITY")
    connection.commit()
    connection.close()


@pytest.fixture
def repository():
    # Creating the repository also creates the table if it does not exist yet.
    repository = PostgresExpenseRepository(TEST_DATABASE_URL)
    delete_all_expenses()

    # The test runs here.
    yield repository

    # Clean up after the test.
    repository.close()


# --- add ------------------------------------------------------------------


def test_add_returns_the_new_expense(repository):
    expense = repository.add(amount_cents=1250, category="Essen", spent_on="2026-10-23")

    assert expense.id == 1
    assert expense.amount_cents == 1250
    assert expense.category == "Essen"
    assert expense.spent_on == "2026-10-23"


def test_add_gives_each_expense_a_new_id(repository):
    first_expense = repository.add(amount_cents=100, category="Essen", spent_on="2026-10-01")
    second_expense = repository.add(amount_cents=200, category="Miete", spent_on="2026-10-02")

    assert first_expense.id == 1
    assert second_expense.id == 2


# --- list -----------------------------------------------------------------


def test_list_is_empty_at_the_start(repository):
    assert repository.list() == []


def test_list_returns_all_expenses_sorted_by_id(repository):
    repository.add(amount_cents=100, category="Essen", spent_on="2026-10-01")
    repository.add(amount_cents=200, category="Miete", spent_on="2026-10-02")

    expenses = repository.list()

    assert len(expenses) == 2
    assert expenses[0].id == 1
    assert expenses[1].id == 2


# --- get ------------------------------------------------------------------


def test_get_returns_the_expense(repository):
    repository.add(amount_cents=1250, category="Essen", spent_on="2026-10-23")

    expense = repository.get(1)

    assert expense is not None
    assert expense.category == "Essen"


def test_get_unknown_id_returns_none(repository):
    assert repository.get(999) is None


# --- delete ---------------------------------------------------------------


def test_delete_removes_the_expense(repository):
    repository.add(amount_cents=1250, category="Essen", spent_on="2026-10-23")

    was_deleted = repository.delete(1)

    assert was_deleted is True
    assert repository.get(1) is None


def test_delete_unknown_id_returns_false(repository):
    assert repository.delete(999) is False


# --- data survives a new repository ---------------------------------------


def test_data_is_still_there_with_a_new_repository(repository):
    # Simulates an app restart: a second repository opens new connections
    # to the same database and must see the data of the first one.
    repository.add(amount_cents=1250, category="Essen", spent_on="2026-10-23")

    second_repository = PostgresExpenseRepository(TEST_DATABASE_URL)
    expenses = second_repository.list()
    second_repository.close()

    assert len(expenses) == 1
    assert expenses[0].category == "Essen"


# --- healthy --------------------------------------------------------------


def test_healthy_is_true_when_the_database_is_reachable(repository):
    assert repository.healthy() is True


def test_healthy_is_false_when_the_connection_is_closed():
    repository = PostgresExpenseRepository(TEST_DATABASE_URL)
    repository.close()

    assert repository.healthy() is False


# --- create_repository ----------------------------------------------------


def test_create_repository_uses_postgres_when_a_database_url_is_set():
    config = Config(database_url=TEST_DATABASE_URL, version="test", log_level="WARNING")

    repository = create_repository(config)

    assert isinstance(repository, PostgresExpenseRepository)
    repository.close()
