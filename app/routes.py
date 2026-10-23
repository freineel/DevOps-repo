from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from app.models import ValidationError

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


# TODO (you): expense endpoints, each with tests in tests/test_expenses.py
#   POST   /api/expenses            validate input, _repo().add(...), 201
#   GET    /api/expenses            optional ?category=...&month=YYYY-MM, filter here
#   DELETE /api/expenses/<int:id>   204, or 404 if unknown
#   GET    /api/expenses/summary    sums per category, computed from _repo().list()
#                                   (test first: empty, mixed, single category)
