# Expense Tracker

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

The rest of the tech stack is decided in week 3 of the course, and this list
will grow with it.

## Setup

    git clone git@github.com:freineel/DevOps-repo.git
    cd DevOps-repo
    python3 -m venv .venv
    source .venv/bin/activate

Installing dependencies and starting the app will be documented here once the
application code exists in week 3.

## Branching strategy

This repository follows GitHub Flow:

- `main` is always in a working state.
- New work happens on a short-lived branch named after its purpose:
  `feature/...`, `fix/...` or `docs/...`.
- Every change reaches `main` through a pull request that says what changed
  and why.
- Branches are deleted after the merge.
- Commit messages are in English and in the imperative mood
  ("Add summary endpoint", not "Added summary endpoint").

