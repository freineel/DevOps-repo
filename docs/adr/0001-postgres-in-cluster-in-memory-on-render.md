# 0001 – Postgres in Compose, Terraform and Kubernetes, in-memory on Render

## Status

accepted (2026-11-22)

## Context

The app stores expenses behind a repository interface. Two backends exist:
an in-memory list and Postgres, chosen by `DATABASE_URL`.

In Kubernetes the app must run with at least two replicas. With the in-memory
store every replica (and every Gunicorn worker) has its own list: an expense
created through one pod is missing when the next request goes to the other
pod. The readiness probe `/ready` would also have nothing real to check.

On Render the project uses the free plan. Render's free Postgres is deleted
after about 30 days, so it would break before the project is graded. A paid
database is not an option for a course project.

Options:

1. Postgres everywhere, including a paid database on Render.
2. Postgres where several processes run (Compose, Terraform, Kubernetes),
   in-memory on Render with exactly one worker.
3. SQLite as a file in the container.

## Decision

We use PostgreSQL 16 in Docker Compose, Terraform and Kubernetes. In
Kubernetes it runs as its own Deployment with a PersistentVolumeClaim and the
`Recreate` strategy (only one Postgres pod may use the volume at a time). On
Render we do not set `DATABASE_URL` and run one Gunicorn worker, so the
in-memory store stays consistent there.

SQLite was rejected: a file inside a container is not shared between replicas
and is lost when the pod is replaced.

## Consequences

Positive:

- Both app replicas in Kubernetes see the same data, a rolling update does not
  lose expenses.
- `/ready` checks a real database, so a pod without a database gets no traffic.
- Render costs nothing and does not break after 30 days.

Negative:

- On Render all expenses are lost on every deploy, restart or sleep of the free
  instance. The public URL is a demo, not a real service.
- Render and the other environments behave differently (one worker, no
  database), so a database bug would not show up on Render.
- Postgres in the cluster is a single pod without backup or replication. If its
  volume is lost, the data is gone.
