# 0002 – Terraform uses a prebuilt image instead of building it

## Status

accepted (2026-11-22)

## Context

The Terraform configuration in `terraform/` starts the local stack (network,
volume, Postgres, app) with the provider `kreuzwerker/docker`. The app needs
a Docker image. The provider can build it itself with a `build {}` block in
`docker_image`.

We tried that first. With provider version 3.9 and Docker Desktop (BuildKit)
the build hung: the log stopped after sending the build context, and after
about four minutes Terraform reported "Plugin did not respond".

Besides the bug there is a general question: who builds the image? The image
is already built by `make docker-build`, by CI and by Render, always from the
same `Dockerfile`.

Options:

1. Build in Terraform (`build {}`) and try to work around the hang.
2. Build the image once with `make docker-build` and let Terraform only use
   the local image `expense-tracker:local`.
3. Push the image to a registry and let Terraform pull it.

## Decision

We build the image with `make docker-build`. Terraform references
`expense-tracker:local` with `keep_locally = true`, so `terraform destroy`
does not delete the image. Terraform only manages infrastructure (network,
volume, containers), not the build.

A registry (option 3) was rejected for now: it needs an account and a token
for a stack that only runs locally.

## Consequences

Positive:

- `terraform apply` is fast and does not hang.
- Clear split: build is one step, infrastructure another ("build once, run
  everywhere").
- The second `terraform plan` shows "No changes", the configuration is
  idempotent.

Negative:

- One extra step: `make docker-build` must run before `terraform apply`,
  otherwise apply fails because the image is missing. The README says so.
- Terraform does not notice when the code changes. After a code change the
  image has to be rebuilt by hand and the container recreated.
- Works only on a machine where the image was built, not on a fresh one
  without the repository.
