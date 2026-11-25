# Abnahme-Checkliste

Kopie von `woche-10-abschlussprojekt/docs/04-abnahme-checkliste.md`, geprüft
am 25.11.2026. Hinter jedem Punkt steht, wo oder wie er geprüft wurde.

## Git und Zusammenarbeit

- [x] Öffentliches GitHub-Repository existiert und ist erreichbar. (`gh repo view`: PUBLIC)
- [x] **`normansuesstrunk`** ist als Collaborator eingeladen (Leserechte genügen). (Einladung offen, seit 14.10.2026)
- [x] `main` ist durch eine Branch Protection Rule gegen direkte Pushes geschützt. (PR Pflicht, Checks Lint/Test/Build image/Trivy scan, gilt auch für Admins)
- [x] Mindestens fünf Pull Requests sind gemergt. (18)
- [x] Jeder dieser PRs hat eine Beschreibung, die *was* und *warum* festhält. (PR-Vorlage seit #5)
- [x] Jeder dieser PRs war zum Merge-Zeitpunkt grün in der CI. (seit #5, als die CI dazukam)
- [x] `CONTRIBUTING.md` beschreibt GitHub Flow, Commit- und Selbstprüfungsregeln.
- [x] Die Commit-Historie zeigt kontinuierliche Arbeit über die Wochen. (14.10. bis 25.11.2026)
- [x] Tag `v1.0.0` ist gesetzt und ein Release mit Anmerkungen ist veröffentlicht.

## Containerisierung

- [x] `Dockerfile` verwendet einen Multi-Stage-Build. (`builder` + `runtime`)
- [x] Das Runtime-Image enthält keine Build-Tools oder pip-Caches. (`--no-cache-dir`, pip entfernt)
- [x] `docker run --rm <image> whoami` gibt nicht `root` aus. (`appuser`)
- [x] `docker build .` läuft ohne Fehler durch.
- [x] `curl localhost:8000/health` liefert im Container `{"status":"ok",...}`.
- [x] `docker-compose.yml` definiert die Dienste `web` und `db`.
- [x] Nach `down` und erneutem `up` sind Daten dank benanntem Volume erhalten. (`db-data`)
- [x] `web` startet erst, wenn `db` gesund ist (`condition: service_healthy`).

## CI-Pipeline

- [x] `.github/workflows/ci.yml` läuft bei jedem Pull Request.
- [x] Die Pipeline enthält einen Lint-Schritt (`ruff check` und Formatprüfung).
- [x] Die Pipeline führt die Tests aus (`pytest`).
- [x] Ein Coverage-Gate von mindestens 80 % ist aktiv (`fail_under = 80`). (aktuell 84.85 %)
- [x] Die Pipeline baut das Container-Image.
- [x] Ein absichtlich fehlerhafter Commit macht die Pipeline nachweislich rot. (PR #6, `docs/evidence/ci-red-blocks-merge.png`)
- [x] Grüner CI-Status ist Voraussetzung zum Mergen.

## CD und Deployment

- [x] `render.yaml` beschreibt den Dienst auf Render.
- [x] Die Anwendung ist unter einer öffentlichen Render-URL erreichbar. (https://expense-tracker-oyhe.onrender.com)
- [x] `GET /health` liefert auf Render `200`.
- [x] Ein Merge auf `main` löst automatisch ein neues Deployment aus. (`cd.yml`)
- [x] `DEPLOYMENT.md` beschreibt Deployment, Rollback und Störungsbehandlung.

## Infrastructure as Code

- [x] Terraform-Konfiguration nutzt den Provider `kreuzwerker/docker`.
- [x] `terraform init` und `terraform validate` laufen fehlerfrei.
- [x] `terraform apply` startet den Container, `terraform destroy` entfernt ihn. (`docs/evidence/terraform-*.txt`)
- [x] Konfiguration nutzt Variablen statt hartkodierter Werte.
- [x] `terraform.tfstate` und `.terraform/` stehen in `.gitignore`. (`terraform/.gitignore`)

## Kubernetes

- [x] Manifeste für Namespace, Deployment und Service liegen unter `k8s/`.
- [x] Der Service bildet Port 80 auf targetPort 8000 ab.
- [x] Das Deployment läuft mit mindestens zwei Replikaten.
- [x] Eine Liveness-Probe prüft `/health`.
- [x] Eine Readiness-Probe prüft `/ready`.
- [x] `kubectl get pods` zeigt alle Replikate als `Running` und `READY 1/1`. (`docs/evidence/k8s-rollout-w08.txt`)

## Monitoring und Sicherheit

- [x] Prometheus scrapt den `/metrics`-Endpunkt.
- [x] Das Target steht in Prometheus unter `Status → Targets` auf UP.
- [x] Ein Grafana-Dashboard „Expense Tracker Overview" existiert.
- [x] Das Dashboard zeigt mindestens Request-Rate, Fehlerrate und Latenz.
- [x] Das Dashboard-JSON ist im Repository versioniert.
- [x] Ein Trivy-Scan läuft in der Pipeline und ist im Log sichtbar. (`trivy-scan.yml`, Pflicht-Check)
- [x] Der Trivy-Schwellwert ist gesetzt und dokumentiert. (ADR 0004, MONITORING.md)
- [x] `git log -p` enthält keine Passwörter, Tokens oder Keys. (`gitleaks git`, 25.11.2026)
- [x] Secrets liegen in GitHub Secrets bzw. der Deploy-Umgebung, nicht im Code.

## Dokumentation

- [x] `README.md` erklärt Was, Warum und einen kopierbaren Schnellstart.
- [x] Eine Architekturübersicht mit C4-Diagramm (Kontext + Container) existiert.
- [x] `DEPLOYMENT.md` ist als abarbeitbares Runbook geschrieben.
- [x] `MONITORING.md` beschreibt Metriken, Dashboard und Schwellwerte.
- [x] Mindestens zwei ADRs unter `docs/adr/` mit den vier Pflichtabschnitten. (4)
- [x] Eine kursfremde Person kann das Projekt allein anhand der Doku starten. (frischer Klon, 25.11.2026)

## Selbsteinschätzung und Abgabe

- [x] Die Tabelle aus dem Bewertungsschema ist ausgefüllt und liegt als `BEWERTUNG.md` im Repository.
- [x] Ein frischer Klon des Repositorys startet allein nach dem README.
- [x] Der Einsatz von KI-Werkzeugen ist deklariert. (README "Author", BEWERTUNG.md)
