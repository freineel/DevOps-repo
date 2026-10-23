import pytest

from app.models import (
    ValidationError,
    validate_amount_cents,
    validate_category,
    validate_month,
    validate_spent_on,
)

# parametrize runs the same test once per value: one line per edge case
# instead of one copy-pasted test function each.


def test_amount_accepts_positive_int():
    assert validate_amount_cents(1250) == 1250


@pytest.mark.parametrize("raw", [0, -5, 12.5, "1250", None, True, False])
def test_amount_rejects_invalid_values(raw):
    with pytest.raises(ValidationError):
        validate_amount_cents(raw)


def test_category_is_stripped():
    assert validate_category("  Essen ") == "Essen"


@pytest.mark.parametrize("raw", ["", "   ", 42, None])
def test_category_rejects_invalid_values(raw):
    with pytest.raises(ValidationError):
        validate_category(raw)


def test_spent_on_accepts_iso_date():
    assert validate_spent_on("2026-10-23") == "2026-10-23"


@pytest.mark.parametrize("raw", ["2026-13-45", "2026-02-30", "gestern", "", 20261023, None])
def test_spent_on_rejects_invalid_values(raw):
    with pytest.raises(ValidationError):
        validate_spent_on(raw)


def test_month_accepts_year_and_month():
    assert validate_month("2026-10") == "2026-10"


@pytest.mark.parametrize("raw", ["2026-13", "2026-1", "10-2026", "2026-10-01", "", None])
def test_month_rejects_invalid_values(raw):
    with pytest.raises(ValidationError):
        validate_month(raw)
