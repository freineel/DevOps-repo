# Kubernetes: local kind cluster

The manifests in this folder run the expense tracker in Kubernetes: two app
replicas behind a Service, plus one Postgres pod with a persistent volume. The
cluster runs locally with [kind](https://kind.sigs.k8s.io/) (Kubernetes in
Docker), so no cloud account is needed.

| File | What it creates |
| --- | --- |
| `00-namespace.yaml` | Namespace `expense-tracker` for all objects |
| `01-configmap.yaml` | Configuration that is not secret (`LOG_LEVEL`, `GUNICORN_WORKERS`) |
| *(no 02 file)* | The Secret is created by `make k8s-secret`, see below |
| `03-postgres.yaml` | PersistentVolumeClaim, Postgres Deployment and Service `expense-tracker-db` |
| `04-deployment.yaml` | App Deployment: 2 replicas, probes, resources, security context |
| `05-service.yaml` | Service `expense-tracker`, port 80 to targetPort 8000 |
| `06-service-nodeport.yaml` | NodePort 30080, access from the host |
| `kind/kind-config.yaml` | kind cluster with 1 control plane and 2 workers (not a manifest) |

The files are numbered because `kubectl apply -f k8s/` applies them in
alphabetical order and the namespace has to exist first.

## Prerequisites

- Docker is running
- `kind` and `kubectl` are installed

## Usage

All commands run in the repository root:

    make k8s-cluster    # create the kind cluster
    make k8s-load       # build expense-tracker:local and load it into kind
    make k8s-deploy     # create the Secret, kubectl apply -f k8s/, wait
    make k8s-status     # pods, deployments, services
    curl http://localhost:30080/health

`make k8s-load` is needed because kind cannot see the images of the local
Docker daemon. The image is copied onto the nodes, and the Deployment uses
`imagePullPolicy: IfNotPresent` so it does not try to pull it from a registry.

## Database password (Secret)

There is no password in this repository. `make k8s-deploy` first runs
`make k8s-secret`, which creates the Secret `expense-tracker-secret`
(`POSTGRES_PASSWORD` and `DATABASE_URL`) directly in the cluster:

    make k8s-secret                      # random password
    make k8s-secret DB_PASSWORD=abc123   # own password (letters and digits only,
                                         # it is put into DATABASE_URL as is)

The Secret is only created if it does not exist yet. Postgres stores the
password on its first start in the volume, so a new password later would lock
the app out. To change it, delete the namespace (this also deletes the data)
and deploy again.

A Secret is only base64-encoded, not encrypted. Anyone who may read Secrets in
the namespace can read the password:

    kubectl -n expense-tracker get secret expense-tracker-secret \
      -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d

## Rolling update and rollback

    make k8s-update VERSION=0.2.0   # build, load, kubectl set image, wait
    curl http://localhost:30080/health   # shows "version": "0.2.0"
    make k8s-rollback               # kubectl rollout undo

No request is lost during an update because of these settings in
`04-deployment.yaml`:

- `maxUnavailable: 0` and `maxSurge: 1`: a new pod is started first, an old one
  is only stopped when the new one is ready.
- Readiness probe on `/ready`: a pod gets traffic only once it can reach the
  database.
- `preStop` hook with `sleep 5`: a stopping pod waits until the Service has
  taken it out of rotation. Without it, 1 of 101 requests failed in a test.

## Probes

| Probe | Path | initialDelaySeconds | periodSeconds | Why |
| --- | --- | --- | --- | --- |
| Liveness | `/health` | 10 | 10 | Process alive? Does not check the database, so a slow database does not cause restarts |
| Readiness | `/ready` | 5 | 5 | Ready for traffic? Checks the database, a pod that is not ready is taken out of the Service |

## Clean up

    kubectl delete namespace expense-tracker   # remove the app, keep the cluster
    make k8s-clean                             # delete the whole kind cluster
