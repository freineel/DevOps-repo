# Local stack of the expense tracker, described with Terraform.
#
# The same two containers as in docker-compose.yml (app + Postgres), but this
# time as declarative infrastructure code: we describe WHAT should exist and
# Terraform works out the steps to get there. The provider talks to the local
# Docker daemon, so no cloud account and no costs are needed.
#
# Usage (Docker must be running):
#   make docker-build      (in the repository root, builds expense-tracker:local)
#   terraform init
#   terraform apply
#   curl http://localhost:8080/health
#   terraform destroy

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    docker = {
      source = "kreuzwerker/docker"
      # Pinned to the 3.x line: minor updates yes, breaking 4.0 no.
      version = "~> 3.0"
    }
  }
}

# Empty block: the provider uses the local Docker socket by default.
provider "docker" {}

# Names in one place, so every resource uses the same prefix. The prefix is
# different from the Compose project, so both stacks can run side by side.
locals {
  network_name  = "${var.name_prefix}-net"
  volume_name   = "${var.name_prefix}-db-data"
  db_container  = "${var.name_prefix}-db"
  web_container = "${var.name_prefix}-web"

  # Inside the shared network the db container name works as hostname.
  database_url = "postgresql://expenses:${var.db_password}@${local.db_container}:5432/expenses"
}

# Own network, so the app can reach the database by its container name.
resource "docker_network" "app" {
  name = local.network_name
}

# Named volume for the Postgres data. It survives a restart of the container,
# but "terraform destroy" deletes it together with the rest of the stack.
resource "docker_volume" "db_data" {
  name = local.volume_name
}

# Fixed major version + alpine variant, same as in docker-compose.yml.
# keep_locally = true: destroy should not delete the image from the machine,
# Compose uses the same image.
resource "docker_image" "postgres" {
  name         = "postgres:16-alpine"
  keep_locally = true
}

# Our own app image. Terraform does not build it, it uses the image that
# "make docker-build" (or CI) already built: build the artefact once, then
# only describe where it runs. Building inside Terraform also hung with the
# BuildKit session of the docker provider on Docker Desktop.
# keep_locally = true: we built the image ourselves, destroy must not delete it.
resource "docker_image" "app" {
  name         = "expense-tracker:${var.image_tag}"
  keep_locally = true
}

resource "docker_container" "db" {
  name  = local.db_container
  image = docker_image.postgres.image_id

  env = [
    "POSTGRES_USER=expenses",
    "POSTGRES_PASSWORD=${var.db_password}",
    "POSTGRES_DB=expenses",
  ]

  networks_advanced {
    name = docker_network.app.name
  }

  volumes {
    volume_name    = docker_volume.db_data.name
    container_path = "/var/lib/postgresql/data"
  }

  # No "ports" block on purpose: only the app needs the database, so it
  # stays unreachable from the host (same as in Compose).

  healthcheck {
    test     = ["CMD-SHELL", "pg_isready -U expenses -d expenses"]
    interval = "5s"
    timeout  = "3s"
    retries  = 10
  }

  # Terraform waits until the healthcheck is green before it continues.
  # Like "depends_on: condition: service_healthy" in Compose: the app creates
  # its table on startup and would crash against a database that still boots.
  wait         = true
  wait_timeout = 60

  restart = "unless-stopped"
}

resource "docker_container" "web" {
  name  = local.web_container
  image = docker_image.app.image_id

  env = [
    "DATABASE_URL=${local.database_url}",
    # Overrides the version baked into the image, shown by /health.
    "APP_VERSION=${var.app_version}",
    "LOG_LEVEL=${var.log_level}",
    # Two workers are fine, both share the same database.
    "GUNICORN_WORKERS=2",
  ]

  networks_advanced {
    name = docker_network.app.name
  }

  ports {
    internal = 8000
    external = var.host_port
  }

  # Explicit order: the app only starts after the database is healthy.
  # The image_id reference above already creates the dependency on the image.
  depends_on = [docker_container.db]

  restart = "unless-stopped"
}
