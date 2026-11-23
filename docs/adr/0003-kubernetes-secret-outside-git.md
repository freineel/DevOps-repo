# 0003 – The Kubernetes Secret is created in the cluster, not stored in Git

## Status

accepted (2026-11-23)

## Context

In Kubernetes the app and Postgres need the database password
(`POSTGRES_PASSWORD`, `DATABASE_URL`). The usual way is a Secret manifest next
to the other manifests, so `kubectl apply -f k8s/` creates everything.

The repository is public. A Secret manifest is only base64-encoded, not
encrypted, so anyone could read the password. Even a placeholder password like
`changeme` in a manifest looks like a leaked secret and teaches the wrong
habit. The project requirements ask for clean secret hygiene
(`git log -p` must not contain passwords).

Options:

1. Secret manifest with a local default password in Git.
2. Create the Secret with `kubectl create secret` from a make target, the
   password comes from a variable or is generated.
3. Encrypted secrets in Git (Sealed Secrets, SOPS) or an external store
   (Vault).

## Decision

We do not store a Secret manifest. `make k8s-secret` creates the Secret
`expense-tracker-secret` directly in the cluster. The password is taken from
`DB_PASSWORD` or generated with `openssl rand -hex 16` (hex, so it can be put
into `DATABASE_URL` without escaping). The Secret is only created if it does
not exist yet. `make k8s-deploy` runs `k8s-secret` first.

Sealed Secrets or Vault (option 3) were rejected: an extra controller or
server for a local kind cluster is more effort than the project needs.

## Consequences

Positive:

- No password in the repository or its history.
- Every cluster gets its own random password.
- Creating the Secret only once matters: Postgres stores the password in its
  volume on the first start, a new password on every deploy would lock the app
  out.

Negative:

- `kubectl apply -f k8s/` alone is no longer enough, the Secret must exist
  first (`make k8s-deploy` handles it).
- The password is not stored anywhere outside the cluster. It can be read back
  with `kubectl get secret`, but if the cluster is deleted it is gone (together
  with the data, so this is acceptable here).
- Changing the password needs a manual step (delete the namespace, which also
  deletes the data).
- Docker Compose and Terraform still use the local default `changeme` when no
  password is given. They only run locally and are not reachable from outside.
