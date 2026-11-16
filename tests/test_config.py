"""Tests for Config.from_env: the app reads its settings from environment variables."""

from app.config import Config


def test_from_env_reads_the_environment_variables(monkeypatch):
    # monkeypatch sets environment variables only for this one test.
    monkeypatch.setenv("DATABASE_URL", "postgresql://user@db:5432/expenses")
    monkeypatch.setenv("APP_VERSION", "1.2.3")
    monkeypatch.setenv("LOG_LEVEL", "debug")

    config = Config.from_env()

    assert config.database_url == "postgresql://user@db:5432/expenses"
    assert config.version == "1.2.3"
    # The log level is always stored in upper case.
    assert config.log_level == "DEBUG"


def test_from_env_uses_defaults_when_nothing_is_set(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("APP_VERSION", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    config = Config.from_env()

    assert config.database_url is None
    assert config.version == "0.0.0-dev"
    assert config.log_level == "INFO"


def test_from_env_treats_an_empty_database_url_as_not_set(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")

    config = Config.from_env()

    assert config.database_url is None
