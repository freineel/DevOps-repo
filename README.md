# Expense Tracker

[![CI](https://github.com/freineel/DevOps-repo/actions/workflows/ci.yml/badge.svg)](https://github.com/freineel/DevOps-repo/actions/workflows/ci.yml)

Expense Tracker is a small web app for recording personal expenses and seeing
where the money goes each month. You enter an amount, a category and a date,
and the app adds them up per category and per month.

This is my semester project for CDS212 (IT Development and Operations) at FHGR.
The course grades the DevOps pipeline around the app (containers, CI/CD,
infrastructure as code, Kubernetes and monitoring), so the app itself stays
small. It has one user and one currency and offers only a REST API. User
accounts, budgets, multiple currencies and a web frontend are out of scope.

## Prerequisites

- Git
- Python 3.12 or newer
- Docker (needed from week 4)

The app uses Flask, served by Gunicorn in the container. Tests run with pytest,
linting with ruff.

## Setup

    git clone git@github.com:freineel/DevOps-repo.git
    cd DevOps-repo
    python3 -m venv .venv
    source .venv/bin/activate
    make install
    make run

`make help` lists all targets (tests, coverage, lint, formatting).

## Container

    docker build -t expense-tracker:local .
    docker run -d -p 8000:8000 --name expense expense-tracker:local
    curl localhost:8000/health

The image is built from `python:3.12-slim` in two stages and runs Gunicorn as
the unprivileged user `appuser`. Compared with a naive Dockerfile
(`python:3.12`, `COPY . .` before `pip install`, single stage, no `USER`):

| Image | Size on disk | Runs as |
| --- | ---: | --- |
| naive | 1.63 GB | root |
| optimized | 188 MB | appuser |

What makes the difference:

- **Slim base image.** `python:3.12-slim` leaves out compilers and system
  tools the app never needs at runtime.
- **Multi-stage build.** Dependencies are installed in a builder stage; only
  the installed packages are copied into the final image, without pip cache
  or build leftovers.
- **Layer order for caching.** `requirements.txt` is copied and installed
  before the application code, so a code change does not trigger a new
  `pip install`.
- **Non-root user and `.dockerignore`.** The process runs as `appuser`, and
  `.git`, `.venv`, tests and `.env` never reach the build context.

## App and database with Docker Compose

    make up      # starts the app (web) and Postgres (db) in the background
    curl localhost:8000/ready
    make down    # stops both, the data stays in the volume db-data

Without `DATABASE_URL` the app keeps its data in memory. Docker Compose sets
`DATABASE_URL`, so the app stores its data in Postgres. The data survives
`make down` and `make up` because it lives in the named volume `db-data`.

## Continuous integration

Every pull request and every push to `main` runs the pipeline in
[`.github/workflows/ci.yml`](.github/workflows/ci.yml):

| Job | What it checks |
| --- | --- |
| Lint | `ruff check` and `ruff format --check` |
| Test | `pytest` against a real Postgres 16, coverage must be at least 80 % |
| Build image | `docker build`, then the container must answer on `/health` |

`main` is protected: a pull request can only be merged when all three jobs
are green.

The tests in `tests/test_postgres_repository.py` need a database. They run in
the pipeline and are skipped locally unless `TEST_DATABASE_URL` is set.

## Deployment

The app runs on Render (free plan): `<APP_URL>`

    curl <APP_URL>/health

After a merge into `main` and a green CI run, the workflow
[`.github/workflows/cd.yml`](.github/workflows/cd.yml) starts a deploy on
Render and then runs [`scripts/smoke-test.sh`](scripts/smoke-test.sh) against
the live app. The Render service is described in [`render.yaml`](render.yaml).

On Render the app runs without a database, so the expenses are kept in memory
and are lost on every deploy or restart. The free instance goes to sleep after
15 minutes, so the first request can take up to a minute.

Setup, configuration, rollback and troubleshooting are described in
[DEPLOYMENT.md](DEPLOYMENT.md).

## Branching strategy

This repository follows GitHub Flow: `main` is always working, every change
goes through a short-lived branch and a pull request with green CI. Branch
names, commit messages and the pull request checklist are described in
[CONTRIBUTING.md](CONTRIBUTING.md).

## Roadmap

| Week | Topic | Result in this repository |
| ---: | --- | --- |
| 1 | DevOps & Linux | Tools set up, topic chosen |
| 2 | Git & GitHub | Repository, branching strategy, first merged pull request |
| 3 | Build processes | App runs locally, first endpoints and tests |
| 4 | Docker | App and database run with `docker compose up` |
| 5 | Continuous integration | Build, tests and lint run on every push |
| 6 | Continuous deployment | App reachable at a public URL |
| 7 | Infrastructure as code | One piece of infrastructure described in Terraform |
| 8 | Kubernetes | Several replicas, rolling updates without downtime |
| 9 | Monitoring & DevSecOps | Grafana dashboard, image scanned with Trivy |
| 10 | Final project | Complete documentation, tag `v1.0.0` |

## Usage

The API listens on port 8000.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/expenses` | Add an expense (`amount_cents`, `category`, `spent_on`) |
| `GET` | `/api/expenses` | List expenses, optionally filtered by `category` or `month` |
| `DELETE` | `/api/expenses/<id>` | Delete an expense |
| `GET` | `/api/expenses/summary` | Totals per category and per month |
| `GET` | `/health` | Liveness check |
| `GET` | `/ready` | Readiness check, includes the database |
| `GET` | `/metrics` | Metrics in Prometheus format |

Amounts are stored in cents (`1250` = 12.50 CHF) to avoid rounding errors.
Dates use the format `YYYY-MM-DD`.

Example:

    curl -X POST localhost:8000/api/expenses \
      -H "Content-Type: application/json" \
      -d '{"amount_cents": 1250, "category": "food", "spent_on": "2026-10-14"}'

    curl "localhost:8000/api/expenses?month=2026-10"

    curl localhost:8000/api/expenses/summary


