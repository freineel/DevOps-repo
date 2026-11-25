# Evidence

Screenshots and command output that show the milestones worked. Each file
was created while doing the step, nothing was edited afterwards.

| File | Shows | Date |
| --- | --- | --- |
| [ci-red-blocks-merge.png](ci-red-blocks-merge.png) | Pull request #6 with a failing Lint job: the merge button is blocked, the three checks are "Required" | 2026-11-16 |
| [render-deploy-live.jpg](render-deploy-live.jpg) | First deploy on Render from the blueprint, status "Live" | 2026-11-18 |
| [render-health.jpg](render-health.jpg) | `/health` on the public Render URL answers `{"status":"ok"}` | 2026-11-18 |
| [render-rollback.jpg](render-rollback.jpg) | Rollback on Render from #12 back to #11 ("Rollback to ... by you"), then live again | 2026-11-23 |
| [terraform-plan-w07.txt](terraform-plan-w07.txt) | `terraform plan`: 6 resources to add | 2026-11-22 |
| [terraform-apply-w07.txt](terraform-apply-w07.txt) | `terraform apply`: 6 resources added, outputs | 2026-11-22 |
| [terraform-destroy-w07.txt](terraform-destroy-w07.txt) | `terraform destroy`: 6 resources destroyed | 2026-11-22 |
| [terraform-idempotent-w10.txt](terraform-idempotent-w10.txt) | `apply`, smoke test, second `plan` with "No changes" (exit code 0), `destroy` | 2026-11-25 |
| [k8s-rollout-w08.txt](k8s-rollout-w08.txt) | kind cluster: 2 app pods `Running 1/1`, self-healing, rolling update and rollback with a request every 0.2 s (incl. the failed tries before the `preStop` hook was added) | 2026-11-22 |
| [../images/grafana-dashboard.jpg](../images/grafana-dashboard.jpg) | Grafana dashboard "Expense Tracker Overview" with test traffic | 2026-11-25 |
| [../images/alert-firing.jpg](../images/alert-firing.jpg) | Alert `ExpenseTrackerDown` firing after `docker compose stop web` | 2026-11-25 |

The security scan results are in the logs of the
[Trivy workflow](https://github.com/freineel/DevOps-repo/actions/workflows/trivy-scan.yml)
and summarised in [MONITORING.md](../../MONITORING.md#security-scan-trivy).
