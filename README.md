# Coldline Task 1.1 — Opening checkpoint

The supplied system runs one bounded asynchronous workflow:

```text
sensor reading -> API -> PostgreSQL -> Redis Streams -> worker -> PostgreSQL
                    |                                      |
                    +---------- local telemetry -----------+
```

The API accepts an out-of-range synthetic shipment reading. PostgreSQL stores its durable state.
Redis Streams carries a provider-neutral `JobQueue` message. The worker calls the deterministic
`ModelProvider` and stores the result. Prometheus, Grafana, and Jaeger provide local diagnostic
evidence.

There is no hosted model, LocalStack service, UI, or agent framework in Task 1.1.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/tripleten-com/ai-system-engineering-curriculum-sprint-1-task-1-1/tree/main)

## Start the system

Prerequisites are Python 3.12 and Docker with Compose v2. The bootstrap installs pinned uv 0.11.8
under `.tools/bin`.

```shell
python infra/scripts/bootstrap.py
./.tools/bin/uv sync --frozen
./.tools/bin/uv run --frozen poe preflight
./.tools/bin/uv run --frozen poe start
./.tools/bin/uv run --frozen poe ready
./.tools/bin/uv run --frozen poe scenario
```

PowerShell and POSIX wrappers are available under `infra/scripts/`. After uv is on `PATH`, the
shorter `uv run --frozen poe <task>` form works.

| Service | Local URL | Purpose |
|---|---|---|
| API | `http://localhost:8000` | Submit and inspect exception workflows |
| Grafana | `http://localhost:3000` | Use the focused diagnostics dashboard |
| Prometheus | `http://localhost:9090` | Query bounded metrics |
| Jaeger | `http://localhost:16686` | Inspect local traces |

Each of these ports can be overridden by setting the matching `COLDLINE_API_HOST_PORT`,
`COLDLINE_GRAFANA_HOST_PORT`, `COLDLINE_PROMETHEUS_HOST_PORT`, or `COLDLINE_JAEGER_HOST_PORT` environment
variable (see `.env.example`) before running `poe start`, if a default collides with something already
running on your machine.

PostgreSQL, Redis, worker metrics, and OTLP remain inside the Compose network. Codespaces uses the
same `compose.yaml` and keeps every forwarded port private.

## Find your way around

Start with the [codebase guide](docs/student/codebase-guide.md). It explains the reading order,
folder responsibilities, runtime flow, five ports, tests, commands, and files that cannot safely
contain comments.

The application source lives in five flat packages:

| Package | Responsibility |
|---|---|
| `api` | HTTP delivery, API use case, configuration, and composition |
| `worker` | Background processing, retries, configuration, and composition |
| `domain` | Provider-neutral contracts, state rules, identity, and redaction |
| `ports` | Exactly five visible application interfaces |
| `adapters` | PostgreSQL, Redis Streams, deterministic model, logs, and traces |

## Common commands

| Command | Use |
|---|---|
| `poe unit` | Run fast isolated behavior tests |
| `poe contract` | Check interfaces, boundaries, submissions, and repository structure |
| `poe smoke` | Check the initialized running platform |
| `poe e2e` | Run the external API-to-worker workflow |
| `poe verify` | Run the public student verification path |
| `poe restart` | Restart API and worker processes |
| `poe stop` | Stop containers and keep named volumes |
| `poe reset` | Stop containers and delete local named volumes |

## Task boundary

Task 1.1 asks you to run and orient to the supplied system, identify the five application ports,
name the seven numbered components of the supplied architecture map in `submission.yaml`, and
record API-side and worker-side baseline trace IDs plus one structured evidence-gap
classification.

Only these paths are student-editable:

- `submission.yaml`
- `docs/student/task-1-1-baseline.md`

The public verifier checks runtime behavior, answer structure, completeness, and allowed paths. It
cannot grade engineering judgment. The instructor reviews the quality of the evidence and reasoning.

### Student walkthrough

1. Start the stack and run `poe ready`.
2. Read the codebase guide and locate the five interfaces under `src/ports/`.
3. Run `poe scenario`.
4. Inspect the returned state, API and worker logs, traces, metrics, and dashboard.
5. Complete the two permitted files. `submission.yaml` records the numbered seven-component
   architecture map, one to five distinct active port interface names, one API trace ID, one worker
   trace ID, controlled evidence-gap values, and one `fidelity_limitation` category; use its inline
   comments for the allowed format and choices.
6. Run `poe verify`.

Use evidence for every claim. Record uncertainty as an `evidence_gap` classification instead of
guessing.

## Operational limits

This local system has no user authentication, authorization, TLS termination, or production secret
store. The Compose PostgreSQL password is a local-only non-secret credential. Never place real
credentials, personal data, or production records in this repository.

Named volumes preserve local PostgreSQL, Redis, Prometheus, Grafana, and Jaeger state across
`poe stop`. The `poe reset` command deletes that state. This topology makes no backup,
replication, high-availability, disaster-recovery, capacity, latency-SLO, or availability claim.
See [JobQueue fidelity](docs/fidelity/JobQueue.md) and
[ModelProvider fidelity](docs/fidelity/ModelProvider.md) for the active adapter boundaries.
