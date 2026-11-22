# Terraform: local stack

This folder describes the local stack of the expense tracker as code: the app
container, a Postgres container, a network and a volume for the database. It
uses the provider [`kreuzwerker/docker`](https://registry.terraform.io/providers/kreuzwerker/docker/latest/docs),
so everything runs on the local Docker daemon. No cloud account is needed.

It is the same stack as in `docker-compose.yml`, but declarative: Terraform
compares the code with the state and only changes what is different.

## Prerequisites

- Docker is running (`docker info` works)
- Terraform >= 1.5 (`terraform version`)
- The app image is built: `make docker-build` in the repository root creates
  `expense-tracker:local`

## Usage

Run all commands inside this folder:

    cd terraform
    terraform init          # downloads the provider (once)
    terraform fmt -check    # code is formatted
    terraform validate      # syntax and references are correct
    terraform plan          # shows what would be created
    terraform apply         # starts the stack
    curl http://localhost:8080/health
    terraform destroy       # removes containers, network and volume again

Terraform does not build the app image, it starts the image that
`make docker-build` built. After a code change:

    make docker-build                              # in the repository root
    terraform apply -replace=docker_container.web  # start a new container

The image is built once and Terraform only describes where it runs. This
keeps building (Docker, CI) and infrastructure (Terraform) apart.

## Variables

| Variable | Default | Meaning |
| --- | --- | --- |
| `host_port` | `8080` | Port on the host, only 1025 to 65535 allowed |
| `image_tag` | `local` | Tag of the image `expense-tracker:<tag>` |
| `app_version` | `0.1.0-terraform` | Version the app shows on `/health` |
| `log_level` | `INFO` | `DEBUG`, `INFO`, `WARNING` or `ERROR` |
| `db_password` | `changeme` | Password of the Postgres user (sensitive) |
| `name_prefix` | `expense-tracker-tf` | Prefix for container, network and volume names |

To change them, copy `terraform.tfvars.example` to `terraform.tfvars`, or pass
a single value on the command line:

    terraform apply -var="host_port=9090"

Port 8080 is used so that this stack can run next to `docker compose`
(port 8000).

## State

Terraform keeps track of what it created in `terraform.tfstate`. The file
contains all values in plain text, including the database password, so it is
listed in `.gitignore` together with `.terraform/` and `*.tfvars`. The lock
file `.terraform.lock.hcl` is committed, it pins the provider version.

The state is local because only one person works on this project. In a team
it would live in a remote backend with locking (for example an S3 bucket), so
two people cannot run `apply` at the same time.
