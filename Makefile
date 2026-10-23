.DEFAULT_GOAL := help

# Docker targets (build/up/down) follow in week 4.
.PHONY: help install run test cov lint fmt clean

help: ## Show this help
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies incl. dev tools
	pip install -r requirements-dev.txt

run: ## Start the development server on port 8000
	flask --app wsgi run --debug --port 8000

test: ## Run the test suite
	pytest

cov: ## Run tests with coverage report (gate: 80 %)
	pytest --cov=app --cov-report=term-missing

lint: ## Check style, imports and formatting
	ruff check .
	ruff format --check .

fmt: ## Auto-fix lint findings and format the code
	ruff check --fix .
	ruff format .

clean: ## Remove caches and test artefacts
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov
	find . -name __pycache__ -type d -exec rm -rf {} +
