# Expense Tracker

[![CI](https://github.com/freineel/DevOps-repo/actions/workflows/ci.yml/badge.svg)](https://github.com/freineel/DevOps-repo/actions/workflows/ci.yml)
[![CD](https://github.com/freineel/DevOps-repo/actions/workflows/cd.yml/badge.svg)](https://github.com/freineel/DevOps-repo/actions/workflows/cd.yml)
[![Trivy scan](https://github.com/freineel/DevOps-repo/actions/workflows/trivy-scan.yml/badge.svg)](https://github.com/freineel/DevOps-repo/actions/workflows/trivy-scan.yml)

Expense Tracker is a small web app for recording personal expenses and seeing
where the money goes each month. You enter an amount, a category and a date,
and the app adds them up per category and per month.

This is my semester project for CDS212 (IT Development and Operations) at FHGR.
The course grades the DevOps pipeline around the app (containers, CI/CD,
infrastructure as code, Kubernetes and monitoring), so the app itself stays
small. It has one user and one currency and offers only a REST API. User
accounts, budgets, multiple currencies and a web frontend are out of scope.

## Prerequisites

- Git, `make` and `curl`
- Python 3.12 or newer (on Ubuntu also `python3.12-venv`)
- Docker with Docker Compose v2 (for the container, Compose and monitoring parts)
- Optional: Terraform 1.9 or newer, kind and kubectl (only for the
  Terraform and Kubernetes parts)

Tested on Ubuntu 24.04 in WSL2 with Docker Desktop.

The app uses Flask, served by Gunicorn in the container. Tests run with pytest,
linting with ruff.

## Setup

    git clone https://github.com/freineel/DevOps-repo.git
    cd DevOps-repo
    python3 -m venv .venv
    source .venv/bin/activate
    make install
    make run

`make run` starts the development server on http://localhost:8000
(`curl localhost:8000/health`). `make test` runs the tests, `make help` lists
all targets.

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
| optimized | 209 MB | appuser |

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
- **Security updates, no pip.** The runtime stage installs Debian security
  updates and removes `pip`, which the app does not need at runtime (see
  [ADR 0004](docs/adr/0004-trivy-gate-threshold.md)).

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
and the Trivy scan (separate workflow, see [Security](#security)) are green.
Pull request #6 shows a red pipeline blocking the merge
([screenshot](docs/evidence/ci-red-blocks-merge.png)).

The tests in `tests/test_postgres_repository.py` need a database. They run in
the pipeline and are skipped locally unless `TEST_DATABASE_URL` is set.

## Deployment

The app runs on Render (free plan): `https://expense-tracker-oyhe.onrender.com`

    curl https://expense-tracker-oyhe.onrender.com/health

After a merge into `main` and a green CI run, the workflow
[`.github/workflows/cd.yml`](.github/workflows/cd.yml) starts a deploy on
Render and then runs [`scripts/smoke-test.sh`](scripts/smoke-test.sh) against
the live app. The Render service is described in [`render.yaml`](render.yaml).

On Render the app runs without a database, so the expenses are kept in memory
and are lost on every deploy or restart. The free instance goes to sleep after
15 minutes, so the first request can take up to a minute.

Setup, configuration, rollback and troubleshooting are described in
[DEPLOYMENT.md](DEPLOYMENT.md).

## Infrastructure as code

The local stack (app, Postgres, network and volume) is also described with
Terraform in [`terraform/`](terraform/README.md), using the local Docker
provider. With Docker running and the image built (`make docker-build`):

    cd terraform
    terraform init
    terraform apply
    curl http://localhost:8080/health
    terraform destroy

The state file stays on the machine and is not committed.

## Kubernetes

The app also runs in a local Kubernetes cluster (kind) with two replicas and a
Postgres pod. The manifests are in [`k8s/`](k8s/README.md):

    make k8s-cluster
    make k8s-load
    make k8s-deploy
    curl http://localhost:30080/health

The database password is not in the repository: `make k8s-deploy` creates the
Secret in the cluster (random, or `DB_PASSWORD=...`).
`make k8s-update VERSION=1.1.0` does a rolling update without downtime,
`make k8s-rollback` goes back to the previous version.

## Monitoring

Prometheus and Grafana run next to the Compose stack:

    make monitoring-up
    make load            # some test traffic for the dashboard
    make monitoring-down

Prometheus (http://localhost:9090) scrapes `/metrics` every 15 seconds and
evaluates four alert rules. Grafana (http://localhost:3000, local login
`admin` / `admin`) shows the dashboard "Expense Tracker Overview" with request
rate, error rate and latency. The dashboard is stored as JSON in
[`monitoring/`](monitoring/) and loaded automatically.
[MONITORING.md](MONITORING.md) explains every panel, the alert thresholds,
the SLOs and what to do when an alert fires.

## Security

The workflow [`.github/workflows/trivy-scan.yml`](.github/workflows/trivy-scan.yml)
scans the Docker image with Trivy on every pull request, on every push to
`main` and once a week. It fails on HIGH or CRITICAL findings that have a fix,
and it also searches the repository for secrets. The threshold is explained
in [ADR 0004](docs/adr/0004-trivy-gate-threshold.md), the current findings in
[MONITORING.md](MONITORING.md#security-scan-trivy). Passwords and tokens are
never stored in the repository.

## Architecture and decisions

[docs/architecture.md](docs/architecture.md) shows how the parts fit together
(C4 context and container diagrams). Important decisions and their trade-offs
are recorded as ADRs in [docs/adr/](docs/adr/).

## Branching strategy

This repository follows GitHub Flow: `main` is always working, every change
goes through a short-lived branch and a pull request with green CI. Branch
names, commit messages and the pull request checklist are described in
[CONTRIBUTING.md](CONTRIBUTING.md).

## Milestones

The project grew with the course, one milestone per week. All of them are
done, the evidence is collected in [docs/evidence/](docs/evidence/).

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

## Documentation

- [docs/architecture.md](docs/architecture.md): C4 context and container diagrams
- [DEPLOYMENT.md](DEPLOYMENT.md): runbook for deployment, rollback and troubleshooting
- [MONITORING.md](MONITORING.md): metrics, dashboard, alerts, SLOs, security scan
- [docs/adr/](docs/adr/): architecture decision records
- [CONTRIBUTING.md](CONTRIBUTING.md): branching, commits, self-review
- [BEWERTUNG.md](BEWERTUNG.md): self-assessment against the course criteria

## Author

| Name | GitHub | Module |
| --- | --- | --- |
| Neel Frei | [@freineel](https://github.com/freineel) | CDS212 IT Development and Operations, FHGR |

**AI tools:** Claude Code (Anthropic) was used during the whole project as an
assistant: to explain course topics, to write first versions of configuration
files, code, tests and documentation, and to run and check commands. All
changes went through pull requests with a green pipeline. Details in
[BEWERTUNG.md](BEWERTUNG.md#eingesetzte-ki-werkzeuge).
