.DEFAULT_GOAL := help

.PHONY: help install run test cov lint fmt clean docker-build up down logs \
        k8s-cluster k8s-load k8s-secret k8s-deploy k8s-status k8s-update k8s-rollback k8s-clean

help: ## Show this help
	@grep -E '^[a-z0-9-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

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

# --- Kubernetes (local kind cluster) -----------------------------------------
# First run: make k8s-cluster -> make k8s-load -> make k8s-deploy -> make k8s-status
K8S_CLUSTER   := expense-tracker
K8S_NAMESPACE := expense-tracker
# New version for k8s-update, e.g. make k8s-update VERSION=0.2.0
VERSION ?= 0.2.0

k8s-cluster: ## Create the kind cluster (1 control plane, 2 workers)
	kind create cluster --config k8s/kind/kind-config.yaml

k8s-load: ## Build expense-tracker:local and load it into the kind cluster
	docker build -t expense-tracker:local --build-arg APP_VERSION=0.1.0 .
	kind load docker-image expense-tracker:local --name $(K8S_CLUSTER)

# The database password is not stored in the repository. k8s-secret creates the
# Secret directly in the cluster, but only if it does not exist yet: Postgres
# keeps the password from its first start in the volume, a new password on every
# deploy would lock the app out. Password: DB_PASSWORD if set, otherwise random
# (hex, so it is safe inside DATABASE_URL).
k8s-secret: ## Create the database Secret once (DB_PASSWORD=... or random)
	kubectl apply -f k8s/00-namespace.yaml
	@if kubectl -n $(K8S_NAMESPACE) get secret expense-tracker-secret >/dev/null 2>&1; then \
		echo "Secret expense-tracker-secret already exists, keeping it"; \
	else \
		pw="$${DB_PASSWORD:-$$(openssl rand -hex 16)}"; \
		kubectl -n $(K8S_NAMESPACE) create secret generic expense-tracker-secret \
			--from-literal=POSTGRES_PASSWORD="$$pw" \
			--from-literal=DATABASE_URL="postgresql://expenses:$$pw@expense-tracker-db:5432/expenses"; \
	fi

k8s-deploy: k8s-secret ## Create the Secret, apply all manifests in k8s/ and wait
	kubectl apply -f k8s/
	kubectl -n $(K8S_NAMESPACE) rollout status deployment/expense-tracker-db
	kubectl -n $(K8S_NAMESPACE) rollout status deployment/expense-tracker

k8s-status: ## Show pods (with node), deployments and services
	kubectl -n $(K8S_NAMESPACE) get pods -o wide
	kubectl -n $(K8S_NAMESPACE) get deployments,services

k8s-update: ## Rolling update to a new image version (VERSION=0.2.0)
	docker build -t expense-tracker:$(VERSION) --build-arg APP_VERSION=$(VERSION) .
	kind load docker-image expense-tracker:$(VERSION) --name $(K8S_CLUSTER)
	kubectl -n $(K8S_NAMESPACE) set image deployment/expense-tracker expense-tracker=expense-tracker:$(VERSION)
	kubectl -n $(K8S_NAMESPACE) rollout status deployment/expense-tracker

k8s-rollback: ## Undo the last rollout of the app
	kubectl -n $(K8S_NAMESPACE) rollout undo deployment/expense-tracker
	kubectl -n $(K8S_NAMESPACE) rollout status deployment/expense-tracker

k8s-clean: ## Delete the kind cluster
	kind delete cluster --name $(K8S_CLUSTER)
