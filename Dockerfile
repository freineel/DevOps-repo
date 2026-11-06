# Multi-stage build: the builder stage installs dependencies, the runtime
# stage only receives the finished packages. No pip cache, no build tools
# -> smaller image and less attack surface.

# Fixed version + slim variant (~150 MB instead of ~1 GB for python:3.12).
# Never :latest, it is not reproducible.
FROM python:3.12-slim AS base
# No .pyc files in the image; unbuffered output so logs show up immediately
# in `docker logs`.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

FROM base AS builder
# Copy only requirements first: this layer stays cached as long as the
# dependencies do not change, even if the code changes.
COPY requirements.txt .
# --prefix collects all packages in one folder that we can copy over later.
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM base AS runtime
# Never run as root: a container escape as root is close to root on the host.
RUN useradd --create-home --uid 10001 appuser

COPY --from=builder /install /usr/local
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser wsgi.py ./

USER appuser
# Documentation only; `docker run -p` actually publishes the port.
EXPOSE 8000

# ARG exists only at build time, ENV also at runtime.
ARG APP_VERSION=0.0.0-dev
ENV APP_VERSION=${APP_VERSION}

# One worker: the in-memory repository lives per process, a second worker
# would hold a second, different expense list. Raise it once Postgres is used.
ENV GUNICORN_WORKERS=1

# Liveness check on /health (no DB). Python instead of curl, because the
# slim image has no curl.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status == 200 else 1)"

# Gunicorn instead of the Flask dev server. 0.0.0.0 so the app is reachable
# from outside the container. sh -c expands ${GUNICORN_WORKERS}; exec makes
# gunicorn PID 1 so it receives SIGTERM on `docker stop` (graceful shutdown).
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS} --access-logfile - wsgi:app"]
