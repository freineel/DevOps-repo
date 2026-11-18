# Deployment runbook

This document explains how to run the Expense Tracker locally and how to
deploy it to [Render](https://render.com) (free plan). It is written so that
someone who does not know the project can follow it step by step.

Live instance: <https://expense-tracker-oyhe.onrender.com>

In this document `<APP_URL>` always means the public URL of the Render
service, without a slash at the end.

How a change gets live:

    pull request -> CI green -> merge to main -> CI on main green
      -> CD workflow calls the Render deploy hook -> Render builds the image
      -> Render switches traffic when /health answers -> smoke test

## A. Prerequisites

Accounts:

- A GitHub account with access to the repository `freineel/DevOps-repo`
  (write access to push branches, only the owner can merge into `main`).
- A Render account. Sign up at https://render.com with "GitHub", then Render
  can see the repository. No credit card is needed for the free plan.

Tools on your computer (Linux or WSL). Check each one:

    git --version        # expected: git version 2.x
    python3 --version    # expected: Python 3.12.x
    curl --version       # expected: curl 7.x or 8.x
    docker --version     # expected: Docker version 2x.x (only for part B, container)

If `python3 -m venv` fails on Ubuntu, install the venv package first:

    sudo apt install python3.12-venv

## B. Local installation

    git clone https://github.com/freineel/DevOps-repo.git
    cd DevOps-repo
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements-dev.txt
    make run

`make run` starts the development server on `http://127.0.0.1:8000`. Open a
second terminal and check it:

    curl http://127.0.0.1:8000/health
    # expected: {"status":"ok","version":"0.0.0-dev"}

The same image that Render runs can also be started locally:

    docker build -t expense-tracker:local .
    docker run --rm -p 8000:8000 expense-tracker:local
    curl http://127.0.0.1:8000/health
    # expected: {"status":"ok","version":"0.0.0-dev"}

Stop the server with `Ctrl+C`.

## C. Configuration variables

The app reads its configuration only from environment variables. The image
is the same everywhere, only the variables are different.

| Name | Default | Secret | Effect |
| --- | --- | --- | --- |
| `DATABASE_URL` | not set | yes | Not set: expenses are kept in memory. Set: the app uses Postgres, e.g. `postgresql://user:password@host:5432/db`. Not set on Render. |
| `APP_VERSION` | `0.0.0-dev` | no | Version shown in `/health` and `/metrics`. On Render set in `render.yaml`. |
| `LOG_LEVEL` | `INFO` | no | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `PORT` | `10000` (Render) | no | Port Render sends the traffic to. Must be `8000`, because Gunicorn listens on 8000. |
| `GUNICORN_WORKERS` | `1` | no | Number of Gunicorn workers. Keep `1` without a database, see part G. |
| `POSTGRES_PASSWORD` | `changeme` | yes | Only for `docker compose` locally, password of the db container. |
| `TEST_DATABASE_URL` | not set | yes | Only for the tests, enables the Postgres tests locally. |

Settings in GitHub (Settings -> Secrets and variables -> Actions):

| Name | Type | Secret | Effect |
| --- | --- | --- | --- |
| `RENDER_DEPLOY_HOOK` | Secret | yes | Deploy hook URL of the Render service. Anyone with this URL can start a deploy. |
| `APP_URL` | Variable | no | Public URL of the service, used by the smoke test. |

Where secrets belong: in GitHub Secrets or in the "Environment" tab of the
Render service. Never in the repository, not in `render.yaml`, not in the
`Dockerfile` and not in this document. A local `.env` file is in
`.gitignore` and is never committed.

## D. Deployment steps (Render Blueprint)

We use the Blueprint (`render.yaml` in the repository root) as the only way.
All settings of the service are in that file.

### D1. One-time setup

1. Log in to https://dashboard.render.com.
2. Click **New** -> **Blueprint**.
3. Connect the GitHub repository `freineel/DevOps-repo`. If it is not in the
   list, click "Configure account" and give Render access to this repository.
4. Give the Blueprint a name, e.g. `expense-tracker`. Branch: `main`.
5. Render shows the service from `render.yaml`:
   - name `expense-tracker`, type Web Service, runtime Docker
   - plan Free, region Frankfurt
   - health check path `/health`
   - environment `PORT=8000`, `GUNICORN_WORKERS=1`, `APP_VERSION`, `LOG_LEVEL`
6. Click **Deploy Blueprint** (or **Apply**). Render now builds the image
   from the `Dockerfile`. This takes about 3 to 5 minutes.
7. Open the service. When the deploy is done, the status says **Live**. The
   URL is shown at the top of the page. This is `<APP_URL>`.

### D2. Connect GitHub Actions (for automatic deploys)

1. In Render, open the service -> **Settings** -> **Deploy Hook**. Copy the
   URL. Treat it like a password.
2. In GitHub, open the repository -> **Settings** -> **Secrets and variables**
   -> **Actions**.
3. Tab **Secrets** -> **New repository secret**: name `RENDER_DEPLOY_HOOK`,
   value = the deploy hook URL.
4. Tab **Variables** -> **New repository variable**: name `APP_URL`, value =
   `<APP_URL>` (with `https://`, without a slash at the end).

### D3. Normal deploy (every time)

Nothing to do by hand. Merge a pull request into `main`. Then:

1. The workflow **CI** runs on `main` (lint, tests, image build).
2. If CI is green, the workflow **CD** starts. It calls the deploy hook,
   waits 3 minutes and runs the smoke test.
3. Render builds the new image and switches to it when `/health` answers.

A deploy can also be started by hand: GitHub -> **Actions** -> **CD** ->
**Run workflow**.

Auto-deploy on every push is turned off in `render.yaml`
(`autoDeployTrigger: "off"`), so code that did not pass CI never gets deployed.

## E. Check after a deploy

1. Health check:

       curl <APP_URL>/health
       # expected: {"status":"ok","version":"0.1.0"}

   If the service was asleep, the first call can take up to a minute.

2. Smoke test (from the repository root):

       bash scripts/smoke-test.sh <APP_URL>

   Expected output (ids can be different):

       Target: <APP_URL>
       == 1/5 /health ==
         OK (attempt 1): {"status":"ok","version":"0.1.0"}
       == 2/5 /ready ==
         OK: {"status":"ready"}
       == 3/5 POST /api/expenses ==
         created expense with id 1
       == 4/5 GET /api/expenses ==
         expense 1 found in the list
       == 5/5 DELETE /api/expenses/1 ==
         deleted expense 1

       SMOKE TEST PASSED

3. Logs in Render: service -> **Logs**. After a good deploy you see the
   Gunicorn start lines and the health checks:

       [INFO] Starting gunicorn 22.x
       [INFO] Listening at: http://0.0.0.0:8000
       [INFO] Booting worker with pid: ...
       "GET /health HTTP/1.1" 200

   Under **Events** the newest deploy is marked as "Deploy live".

4. In GitHub -> **Actions** the newest run of **CD** is green.

## F. Rollback

When a deploy is broken, go back to the last version that worked.

1. In Render, open the service -> **Events**.
2. Find the last deploy that worked (marked "Deploy live" before the broken one).
3. Click **Rollback** next to it and confirm. Render starts the old image
   again, no new build is needed.
4. Check it:

       curl <APP_URL>/health
       # expected: {"status":"ok", ...} with HTTP 200
       bash scripts/smoke-test.sh <APP_URL>
       # expected: SMOKE TEST PASSED

5. Fix the problem in the code: revert the broken commit on a branch
   (`git revert <commit>`) and merge it with a pull request. Otherwise the
   next merge into `main` deploys the broken code again.

Limits of a rollback:

- Without a database all expenses are in memory. Every deploy, rollback,
  restart or sleep of the free instance deletes them. A rollback cannot bring
  them back.
- With a database a rollback only changes the code, not the data or the
  table structure. If the new version changed the schema, the old version may
  not work with it. Then a fix forward (new version) is needed instead.
- Changed environment variables are not rolled back. Change them back in the
  "Environment" tab if needed.

## G. Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Deploy never gets "Live", log shows "No open ports detected" or the health check times out | Render sends traffic to port 10000, but Gunicorn listens on 8000 | Set `PORT=8000` in `render.yaml` (or in the Environment tab) and deploy again |
| Deploy fails with "health check failed" although the app starts | Health check path is set to `/ready` and the database is not reachable, so `/ready` answers 503 | Set the health check path to `/health`. `/health` does not use the database |
| First request takes 30 to 60 seconds, browser shows a loading page | Free instance went to sleep after 15 minutes without requests (cold start) | Not an outage. Wait and call again. The smoke test tries `/health` several times for this reason |
| An expense was created (201), but `GET` or `DELETE` gives 404 a moment later | More than one Gunicorn worker without database: every worker has its own list in memory | Set `GUNICORN_WORKERS=1`, or use a database |
| All expenses are gone after a while | In-memory storage: the data is lost on every deploy, restart or sleep | Expected on the free plan without database (see part F) |
| CD workflow fails with "The secret RENDER_DEPLOY_HOOK is not set" | Secret missing in GitHub or wrong name | Create the secret as in D2, name exactly `RENDER_DEPLOY_HOOK` |
| CD step "Trigger deploy" fails with `401` | Deploy hook URL is wrong or was created again in Render | Copy the current hook from Render and update the secret |
| Smoke test fails with "/health did not answer with 200" | Wrong `APP_URL` (e.g. typo or slash at the end) or the build on Render takes longer than usual | Check the variable `APP_URL`, look at the Render logs, run the CD workflow again by hand |

If a secret was ever printed in a log or committed: create a new one at once
(Render -> Settings -> Deploy Hook -> regenerate, then update the GitHub
secret). Deleting the commit is not enough, the old value stays in the Git
history.

## H. Contact and escalation

| Role | Who | How |
| --- | --- | --- |
| Service owner | Project owner (GitHub user `freineel`) | GitHub issue in this repository |
| Render account | Project owner | Render dashboard |
| Course lead (only for grading questions) | GitHub user `normansuesstrunk` | Course forum |

Escalation:

1. Follow parts E and G of this document first.
2. Not solved after 30 minutes: roll back (part F) so the service works again.
3. Then open a GitHub issue with the label `bug`: what was deployed (commit),
   what happens, logs from Render and the failed CD run.
4. Render itself is down (see https://status.render.com): wait, nothing to do
   in this project.
