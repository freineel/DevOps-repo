"""Tests for InMemoryExpenseRepository and for choosing the repository."""

from app.config import Config
from app.repository import InMemoryExpenseRepository, create_repository


def test_get_returns_the_expense():
    repository = InMemoryExpenseRepository()
    repository.add(amount_cents=1250, category="Essen", spent_on="2026-10-23")

    expense = repository.get(1)

    assert expense is not None
    assert expense.category == "Essen"


def test_get_unknown_id_returns_none():
    repository = InMemoryExpenseRepository()

    assert repository.get(999) is None


def test_create_repository_uses_memory_when_no_database_url_is_set():
    config = Config(database_url=None, version="test", log_level="WARNING")

    repository = create_repository(config)

    assert isinstance(repository, InMemoryExpenseRepository)
