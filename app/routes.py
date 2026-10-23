from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.models import (
    ValidationError,
    validate_amount_cents,
    validate_category,
    validate_month,
    validate_spent_on,
)

bp = Blueprint("main", __name__)


def _repo():
    return current_app.extensions["repository"]


def _config():
    return current_app.extensions["app_config"]


@bp.errorhandler(ValidationError)
def _handle_validation_error(exc: ValidationError):
    return jsonify(error=str(exc)), 400


@bp.get("/health")
def health():
    """Liveness: is the process up? Must not touch the database.

    Kubernetes restarts the container when this fails, so a slow database
    must never be able to trigger a restart loop.
    """
    return jsonify(status="ok", version=_config().version)


@bp.get("/ready")
def ready():
    """Readiness: can this instance serve traffic? Checks dependencies."""
    if _repo().healthy():
        return jsonify(status="ready")
    return jsonify(status="unavailable"), 503


@bp.post("/api/expenses")
def create_expense():
    # silent=True: a missing or broken JSON body yields None instead of an
    # exception, so the validators below answer with a clear 400 message.
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    expense = _repo().add(
        amount_cents=validate_amount_cents(payload.get("amount_cents")),
        category=validate_category(payload.get("category")),
        spent_on=validate_spent_on(payload.get("spent_on")),
    )
    return jsonify(expense.to_dict()), 201


@bp.get("/api/expenses")
def list_expenses():
    # Filtering happens here on top of list(), not in the repository, so the
    # Postgres backend in week 4 does not need extra methods.
    expenses = _repo().list()

    category = request.args.get("category")
    if category is not None:
        category = validate_category(category)
        expenses = [e for e in expenses if e.category == category]

    month = request.args.get("month")
    if month is not None:
        month = validate_month(month)
        # spent_on is always YYYY-MM-DD, so "2026-10" is an exact prefix.
        expenses = [e for e in expenses if e.spent_on.startswith(month)]

    return jsonify([e.to_dict() for e in expenses])


@bp.get("/api/expenses/summary")
def expenses_summary():
    """Sums per category and per month, computed from list()."""
    by_category: dict[str, int] = {}
    by_month: dict[str, int] = {}
    for e in _repo().list():
        by_category[e.category] = by_category.get(e.category, 0) + e.amount_cents
        month = e.spent_on[:7]  # "2026-10-23" -> "2026-10"
        by_month[month] = by_month.get(month, 0) + e.amount_cents
    return jsonify(
        total_cents=sum(by_category.values()),
        by_category=by_category,
        by_month=by_month,
    )


@bp.delete("/api/expenses/<int:expense_id>")
def delete_expense(expense_id: int):
    if not _repo().delete(expense_id):
        return jsonify(error="expense not found"), 404
    # 204 No Content: success, deliberately without a body.
    return "", 204
