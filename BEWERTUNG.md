# Selbsteinschätzung

**Projekt:** Expense Tracker (`freineel/DevOps-repo`)
**Autor:** Neel Frei (`@freineel`)
**Abgabe-Tag:** `v1.0.0` vom 25.11.2026 (Frist: 18.01.2027, 12:00 Uhr)

Grundlage: `woche-10-abschlussprojekt/docs/03-bewertungsschema.md`. Die
abgehakte Abnahme-Checkliste liegt in [abnahme-checkliste.md](abnahme-checkliste.md).

## Punkte je Kriterium

| Kriterium | max | Selbsteinschätzung | Beleg (Datei, Link, Commit) |
|---|---:|---:|---|
| Git und Arbeitsweise | 12 | 11 | `main` geschützt (PR + Pflicht-Checks, [Screenshot](docs/evidence/ci-red-blocks-merge.png)); 17 gemergte [Pull Requests](https://github.com/freineel/DevOps-repo/pulls?q=is%3Apr+is%3Amerged) mit Was/Warum/Selbstprüfung; [CONTRIBUTING.md](CONTRIBUTING.md); kurze `feature/`-, `fix/`-, `docs/`-Branches; Commits vom 14.10. bis 25.11.2026 verteilt auf alle Wochen. Abzug: Conventional Commits erst ab Woche 5 (vorher `Add …` ohne Typ). |
| Containerisierung | 12 | 11 | [Dockerfile](Dockerfile) mit Multi-Stage, `USER appuser`, `HEALTHCHECK`, ohne pip und pip-Cache; [docker-compose.yml](docker-compose.yml) mit `web` + `db`, `condition: service_healthy`, Volume `db-data` (Persistenz über `down`/`up` am 25.11. im frischen Klon geprüft). Abzug: Image mit 209 MB schlank, aber nicht minimal (kein distroless). |
| CI-Pipeline | 14 | 14 | [ci.yml](.github/workflows/ci.yml): Lint, Test gegen Postgres 16, Coverage-Gate 80 % ([pyproject.toml](pyproject.toml)), Build mit Start-Check; pip-Cache, Lint und Test parallel; rot blockiert Merge nachgewiesen mit [PR #6](https://github.com/freineel/DevOps-repo/pull/6) und [Screenshot](docs/evidence/ci-red-blocks-merge.png). |
| CD und Deployment | 12 | 12 | [render.yaml](render.yaml), [cd.yml](.github/workflows/cd.yml) (Deploy Hook nach grüner CI auf `main`, danach Smoke-Test); live unter https://expense-tracker-oyhe.onrender.com/health; Rollback erprobt ([Screenshot](docs/evidence/render-rollback.jpg)); [DEPLOYMENT.md](DEPLOYMENT.md) als Runbook (Setup, Variablen, Deploy, Prüfung, Rollback, Störungen). |
| Infrastructure as Code | 10 | 10 | [terraform/](terraform/) mit `kreuzwerker/docker`: Netzwerk, Volume, Postgres, App; Variablen mit Validierung und Beschreibung, `db_password` sensitive, [Outputs](terraform/outputs.tf); State in `.gitignore`; `apply`/`destroy` und zweiter `plan` mit "No changes" in [docs/evidence/](docs/evidence/terraform-idempotent-w10.txt). |
| Kubernetes | 14 | 14 | [k8s/](k8s/): Namespace, ConfigMap, Postgres mit PVC, Deployment mit 2 Replikaten, Liveness `/health` + Readiness `/ready`, Requests/Limits, `preStop`, `securityContext`, Service 80 → 8000; Rolling Update 107/107 und Rollback 108/108 Requests ohne Fehler ([Protokoll](docs/evidence/k8s-rollout-w08.txt)); Secret nicht im Repo ([ADR 0003](docs/adr/0003-kubernetes-secret-outside-git.md)). |
| Monitoring und Sicherheit | 14 | 14 | Prometheus scrapt `web:8000/metrics`, Target UP; Dashboard "Expense Tracker Overview" als JSON in [monitoring/](monitoring/grafana/dashboards/expense-tracker-overview.json) ([Screenshot](docs/images/grafana-dashboard.jpg)); 4 Alarmregeln, `ExpenseTrackerDown` auf Firing gebracht ([Screenshot](docs/images/alert-firing.jpg)); Trivy in [trivy-scan.yml](.github/workflows/trivy-scan.yml) mit dokumentiertem Schwellwert ([ADR 0004](docs/adr/0004-trivy-gate-threshold.md), [MONITORING.md](MONITORING.md#security-scan-trivy)); Secret-Scan in der Pipeline, `gitleaks` über die ganze Historie ohne Fund. |
| Dokumentation | 12 | 12 | [README.md](README.md), [C4 Kontext + Container](docs/architecture.md), [DEPLOYMENT.md](DEPLOYMENT.md), [MONITORING.md](MONITORING.md), 4 [ADRs](docs/adr/) mit verworfenen Alternativen und negativen Folgen; frischer Klon über HTTPS nur nach README am 25.11.2026 erfolgreich (Install, Lint, Tests, `make run`, Compose, Monitoring). |
| **Summe** | **100** | **98** | |

## Bewusst offen gelassen

- **Kein Alertmanager.** Die Alarme sind nur in Prometheus sichtbar, es gibt
  keine Benachrichtigung per Mail oder Chat. Für ein lokales Ein-Personen-Projekt
  wäre das zusätzliche Konfiguration ohne Empfänger.
- **Monitoring nur lokal.** Prometheus und Grafana laufen neben Docker Compose,
  nicht für die Render-Instanz. Ein gehostetes Prometheus wäre kostenpflichtig;
  Render wird nach jedem Deploy mit dem Smoke-Test geprüft.
- **Render ohne Datenbank.** Auf Render läuft die App mit dem In-Memory-Speicher,
  die Daten gehen bei jedem Deploy verloren. Begründung in
  [ADR 0001](docs/adr/0001-postgres-in-cluster-in-memory-on-render.md).
- **53 HIGH-Funde ohne Fix im Basis-Image.** Bewusst akzeptiert, Bewertung je
  Paket in [MONITORING.md](MONITORING.md#security-scan-trivy).
- **Trivy als eigener Workflow, nicht in `ci.yml`.** Er läuft bei jedem Pull
  Request genauso und erscheint als eigener Check "Trivy scan".
- **Kann-Punkte nicht umgesetzt:** keine zweite Umgebung (Staging),
  keine Datenbank-Migrationen, keine Autoskalierung, keine SBOM.
- **Commit-Historie nicht umgeschrieben.** Die frühen Commits ohne
  Conventional-Commit-Typ bleiben so, ein Umschreiben würde die Pull Requests
  zerstören.

## Eingesetzte KI-Werkzeuge

Deklarationspflicht gemäss den Regeln zu KI-Werkzeugen im Kurs-README.

| Werkzeug | Wofür eingesetzt |
|---|---|
| Claude Code (Anthropic) | Über das ganze Projekt als Assistent: Kursstoff erklären und Wochenzusammenfassungen erstellen; erste Fassungen von Konfigurationsdateien (Dockerfile, Compose, GitHub-Actions-Workflows, Terraform, Kubernetes-Manifeste, Prometheus/Grafana), von Teilen des App-Codes und der Tests sowie Entwürfe der Dokumentation (README, DEPLOYMENT.md, MONITORING.md, ADRs); Befehle ausführen und Ergebnisse prüfen (Tests, Trivy- und gitleaks-Scans, Terraform- und Kubernetes-Läufe, Screenshots). Jede Änderung lief über einen Pull Request mit grüner Pipeline. |
