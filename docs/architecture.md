# Architecture

## Overview

The expense tracker is one Flask app (served by Gunicorn on port 8000) and one
PostgreSQL 16 database. The app talks to the database only through
`DATABASE_URL`; without it the app uses an in-memory store. The same Docker
image runs in four places: Docker Compose (local development), Terraform
(local, IaC), a kind cluster (Kubernetes) and Render (public URL). GitHub
Actions tests, scans and builds every change and starts the deploy to Render.
Prometheus and Grafana watch the app locally (see [MONITORING.md](../MONITORING.md)).

The main decisions are written down as ADRs in [docs/adr/](adr/).

## C4 level 1: context

Who uses the system and which other systems does it talk to?

```mermaid
graph TD
    user["User<br/>(Person)"]
    dev["Developer<br/>(Person)"]
    system["Expense Tracker<br/>(Software system)"]
    github["GitHub + GitHub Actions<br/>(Code, CI/CD)"]
    render["Render<br/>(Cloud hosting)"]
    monitoring["Prometheus + Grafana<br/>(Monitoring, local)"]

    user -->|"records and reads expenses<br/>REST API, HTTPS"| system
    dev -->|"pushes code, opens pull requests"| github
    github -->|"tests, scans, builds and deploys"| render
    render -->|"runs"| system
    monitoring -->|"scrapes /metrics"| system
    dev -->|"reads dashboard and alerts"| monitoring
```

## C4 level 2: containers

Which separately deployable parts does the system have? The first diagram
shows the Kubernetes setup, it is the most complete one for the app (two
replicas).

```mermaid
graph TD
    user["User"]

    subgraph cluster["Kubernetes namespace: expense-tracker (kind)"]
        svc["Service expense-tracker<br/>port 80 to 8000<br/>NodePort 30080"]
        web["Web app<br/>Python 3.12, Flask, Gunicorn<br/>port 8000, 2 replicas"]
        db[("PostgreSQL 16<br/>PersistentVolumeClaim")]
        secret["Secret<br/>DATABASE_URL, POSTGRES_PASSWORD<br/>(not in Git)"]
    end

    user -->|"HTTP, JSON"| svc
    svc --> web
    web -->|"SQL over DATABASE_URL"| db
    secret -.->|"environment variables"| web
    secret -.->|"environment variables"| db
```

Monitoring runs with Docker Compose (`make monitoring-up`), next to the same
web app and database:

```mermaid
graph TD
    dev["Developer"]

    subgraph compose["Docker Compose: docker-compose.yml + docker-compose.monitoring.yml"]
        web["Web app<br/>port 8000, /metrics"]
        db[("PostgreSQL 16<br/>volume db-data")]
        prom["Prometheus v2.55<br/>port 9090, alert rules"]
        graf["Grafana 11.3<br/>port 3000, dashboard from the repo"]
    end

    web -->|"SQL"| db
    prom -->|"GET /metrics every 15 s"| web
    graf -->|"PromQL"| prom
    dev -->|"dashboard"| graf
    dev -->|"alerts"| prom
```

The same containers in the other environments:

| Environment | Web app | Database | Started with |
| --- | --- | --- | --- |
| Docker Compose | service `web`, port 8000 | service `db`, volume `db-data` | `make up`, with monitoring `make monitoring-up` |
| Terraform | container `expense-tracker-tf-web`, port 8080 | container `expense-tracker-tf-db` | `terraform apply` |
| Kubernetes (kind) | Deployment, 2 replicas, NodePort 30080 | Deployment + PVC | `make k8s-deploy` |
| Render | web service, free plan | none, in-memory store | merge to `main` (CD workflow) |

## Health endpoints

| Path | Meaning | Used by |
| --- | --- | --- |
| `/health` | the process runs (no database check) | liveness probe, Render health check, Docker healthcheck |
| `/ready` | the app can reach its database | readiness probe, smoke test |
| `/metrics` | Prometheus metrics | Prometheus |

## Main decisions

| Topic | Decision | ADR |
| --- | --- | --- |
| Database | Postgres everywhere with more than one process, in-memory only on Render | [0001](adr/0001-postgres-in-cluster-in-memory-on-render.md) |
| Terraform | Terraform uses the image from `make docker-build`, it does not build it | [0002](adr/0002-terraform-uses-prebuilt-image.md) |
| Secrets | The Kubernetes Secret is created in the cluster, not stored in Git | [0003](adr/0003-kubernetes-secret-outside-git.md) |
| Security scan | Trivy gate on HIGH/CRITICAL findings that have a fix | [0004](adr/0004-trivy-gate-threshold.md) |
