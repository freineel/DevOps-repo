.DEFAULT_GOAL := help

.PHONY: help install run test cov lint fmt clean docker-build up down logs

help: ## Show this help
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

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

docker-build: ## Build the Docker image expense-tracker:local
	docker build -t expense-tracker:local .

up: ## Start app and database with Docker Compose
	docker compose up --build --detach

down: ## Stop app and database (data stays in the volume)
	docker compose down

logs: ## Show the logs of app and database
	docker compose logs --follow
