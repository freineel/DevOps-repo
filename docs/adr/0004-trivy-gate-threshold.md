# 0004 – Trivy gate: HIGH and CRITICAL, only findings with a fix

## Status

accepted (2026-11-25)

## Context

The workflow `.github/workflows/trivy-scan.yml` scans the Docker image with
Trivy. The scan only protects us if it can stop a pull request, so it needs an
exit code and a threshold.

The first scan of our image (2026-11-25) showed 224 findings in the Debian
packages of `python:3.12-slim` (54 HIGH, no CRITICAL) and 6 in `pip`. Almost
all Debian findings have no fixed version yet ("affected"). Exactly one HIGH
finding (`libzstd1`) had a fix in Debian, but the official base image was not
rebuilt with it yet, so `docker build --pull` did not help.

Options for the threshold:

1. Only `CRITICAL`.
2. `HIGH,CRITICAL` with `--ignore-unfixed`.
3. `HIGH,CRITICAL` including findings without a fix.

Options for a fixable finding that the base image does not contain yet:

a. `apt-get upgrade` in the Dockerfile.
b. Put the CVE into `.trivyignore`.
c. Wait for a new base image and keep the pipeline red until then.

## Decision

Threshold: option 2. The gate fails on HIGH and CRITICAL findings that have a
fixed version. Option 1 lets HIGH findings through that we could fix with an
update. Option 3 would make every pull request red because of findings nobody
can fix right now, and a gate that is always red gets ignored.

Base image: option a. The runtime stage runs `apt-get upgrade` and deletes the
apt lists in the same layer. `.trivyignore` (option b) is meant for findings
that cannot be fixed or do not apply, not for ones with an available update.
Waiting (option c) blocks all work for an unknown time.

In the same step `pip` is removed from the runtime image. The app never calls
it, and with it the 6 pip findings are gone.

## Consequences

Positive:

- The gate is green as long as everything fixable is fixed, and turns red
  as soon as a fix exists that we do not have.
- The full list (all severities, also without fix) is still printed in the
  log by the "Report all findings" step.
- The weekly scheduled run catches new CVEs even without code changes.

Negative:

- The 53 HIGH findings without a fix stay in the image. We accept this for
  now, because as far as we can see none of them is reachable through our
  app (details per package in MONITORING.md): most are in tools the app never
  runs (`util-linux` mount tools, `login`, `acl`, `systemd`, `ncurses`,
  `perl`), the OpenSSL ones only affect QUIC, and the SQLite ones need FTS5 or
  session changesets, while the app uses neither QUIC nor SQLite. They are
  re-checked with every run.
- `apt-get upgrade` makes the build less reproducible: the same Dockerfile
  can give slightly different packages on different days. The build also
  takes a few seconds longer and the image grew by about 2 MB.
- Without `pip` nobody can install a package inside the running container for
  debugging. A new image has to be built instead.
