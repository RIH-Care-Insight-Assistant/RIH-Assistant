# Local Kubernetes deployment (kind) — Phase 9

Local only: one kind cluster on this machine, frontend published on `127.0.0.1:8090`.
No managed cloud, no registry, no cost. Evidence: [`../evidence/k8s/`](../evidence/k8s/).

## Requirements

- Docker Desktop (or Docker Engine), `kubectl` (v1.36 used here, with built-in Kustomize).
- kind v0.33.0. It was installed user-locally from the official release with its published
  SHA-256 verified; `scripts/k8s.py` finds it on `PATH`, in `RIH_KIND`, or in `~/.rih-tools/`.
- Images built locally: `docker compose build` (produces `rih-backend:local`, `rih-frontend:local`).

## Lifecycle

```bash
docker compose build
python scripts/k8s.py up          # create cluster "rih", load images, apply deploy/k8s/overlays/local, wait
python scripts/k8s.py status      # deployments, pods, services, PVC, NetworkPolicies
python scripts/k8s.py verify      # workloads, security contexts, workflows, NetworkPolicies, red team
python scripts/k8s.py rollout     # rollout, failing rollout, rollback, restore (availability measured)
python scripts/k8s.py recovery    # pod deletion, crash restart, readiness-gated endpoints
python scripts/k8s.py down        # delete the cluster
```

Every `kubectl` call uses `--context kind-rih`, so other clusters are never touched. Add
`--write` to `verify`, `rollout` or `recovery` to record evidence.

`up` writes `deploy/k8s/overlays/local/bootstrap.env` (gitignored) with a random password for
the first admin, `k8s.admin`; Kustomize turns it into the `rih-bootstrap` Secret. The API creates
that admin only while no staff account exists. To sign in, read the password from that file.

## What is deployed

| Object | Settings |
|---|---|
| Namespace `rih` | Pod Security Admission `restricted` (enforce, warn, audit) |
| Deployment `rih-backend` | 1 replica (SQLite on a ReadWriteOnce PVC; in-memory rate limits); RollingUpdate `maxSurge 1, maxUnavailable 0`; startup, liveness (`/api/v1/health`) and readiness (`/api/v1/ready`) probes; requests 100m/256Mi, limits 1 CPU/768Mi; uid 10001, read-only root, all capabilities dropped, RuntimeDefault seccomp, no service-account token; `preStop` 5 s drain |
| Deployment `rih-frontend` | 2 replicas, PodDisruptionBudget `minAvailable 1`; nginx uid 101, read-only root with emptyDirs for `/tmp` and the rendered config; probes on `/healthz`; `preStop` 5 s drain |
| Services | `rih-backend` ClusterIP :8000; `rih-frontend` NodePort 30080 → host `127.0.0.1:8090` |
| ConfigMap `rih-backend-config` | Environment (production, model features off, simulation off, origins for 8090) |
| Secret `rih-bootstrap` | First-admin username and random password (generated, not committed) |
| PVC `rih-data` | 1 Gi, kind's default `standard` StorageClass |
| NetworkPolicies | `default-deny-all` (ingress and egress); `allow-dns-egress`; `frontend-ingress` (:8080); `frontend-to-backend` (:8000); `backend-ingress-from-frontend` — the backend has no internet egress |

## NetworkPolicy enforcement

kind's default CNI (kindnet) enforces NetworkPolicies. `verify` checks it empirically rather than
trusting the manifests:

| Probe | Result |
|---|---|
| frontend pod → backend Service | allowed |
| `intruder` pod in the same namespace → backend Service | blocked (timeout) |
| backend pod → `1.1.1.1:443` | blocked (timeout) |
| pod in a namespace without policies → `1.1.1.1:443` (control) | connected |
| that control pod → backend Service | blocked (backend ingress allows only the frontend) |

## Rollout and rollback procedure

1. Build and load the new image: `docker tag rih-backend:local rih-backend:v2` (or build a new
   one), then `kind load docker-image rih-backend:v2 --name rih`.
2. Roll out: `kubectl --context kind-rih -n rih set image deployment/rih-backend api=rih-backend:v2`
   and `kubectl ... rollout status deployment/rih-backend`.
3. If it stalls or misbehaves: `kubectl ... rollout undo deployment/rih-backend`
   (`rollout history` lists revisions; `revisionHistoryLimit` keeps the last 5).

Recorded results ([rollout.json](../evidence/k8s/rollout.json)): a good rollout, a deliberately
broken rollout (image that does not exist, so the new pod never becomes ready), `rollout undo`
and an image restore, each with 0 failed requests while polling the API every 0.2 s through the
NodePort. The broken rollout never took traffic because `maxUnavailable: 0` kept the old pod.

**Finding fixed here:** before the `preStop` drain delay, one rollout run had 2 of 15 requests
fail with 503 while endpoint removal propagated to the proxy; three runs after the fix had none.

## Recovery

Recorded results ([recovery.json](../evidence/k8s/recovery.json)): deleting the backend pod →
replacement healthy in about 1.5 s with conversation data intact (PVC); deleting a frontend pod →
100% availability through the second replica; killing the API process → container restarted by
the kubelet; the backend endpoint is ready only while `/api/v1/ready` passes.

## Limits of this deployment

Single node; SQLite and in-memory rate limits mean one API replica; plain HTTP on loopback with
`RIH_COOKIE_SECURE=false`; images are loaded from the local Docker cache (no registry); no
Ingress controller or TLS. See [`../limitations.md`](../limitations.md).
