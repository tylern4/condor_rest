# htcondor-rest

A REST API for HTCondor, exposing the `htcondor2` Python bindings over HTTP. It bundles:

- a **FastAPI server** that wraps `condor_q`, `condor_history`, `condor_submit`, `condor_rm`, `condor_hold`, `condor_status`, and the rest of the HTCondor admin surface,
- a typed **Python client library** (`htcondor_rest.client.CondorClient`),
- Prometheus metrics under `/metrics`,
- Docker images for a standalone HTCondor pool and for deployment on **Spin@NERSC**.

## How it works

The server runs *inside* an HTCondor pool (either a full pool or a mini single-container pool). Every endpoint translates HTTP requests into calls against the `htcondor2` Python API, so the server talks directly to the local `condor_schedd`/`collector`/`negotiator` daemons. Clients authenticate with a bearer token; all endpoints except `/metrics` require one.

```
+----------------+        Bearer token        +----------------------+        HTCondor daemons
| CondorClient   |  ----------------------->  |  FastAPI app (uvicorn |  ---------------------->  condor_schedd
|                |  HTTP/JSON                 |  / gunicorn)          |  htcondor2 bindings      condor_collector
+----------------+                            |  port 8008            |                          condor_negotiator
                                               +----------------------+
```

## Repository layout

| Path | Purpose |
|------|---------|
| `src/htcondor_rest/app.py` | The FastAPI application with all API routes |
| `src/htcondor_rest/models/__init__.py` | Pydantic request/response models |
| `src/htcondor_rest/client.py` | `CondorClient` HTTP client |
| `htcondor_configs/` | HTCondor config and container startup scripts |
| `Dockerfile` | Full pool image (supervisord) |
| `spin.Dockerfile` | Single-container mini-pool image for Spin@NERSC |
| `tests/` | API and client tests (dummy `htcondor2` module, run in CI) |

## Quickstart

### Run the server

The server needs a reachable HTCondor pool. The easiest way to try everything is the Spin image (below), which runs a whole mini-pool in one container. To run just the server against an existing pool:

```bash
uv sync
condor_status   # must talk to your pool first, or set CONDOR_CONFIG
uvicorn htcondor_rest.app:app --host 0.0.0.0 --port 8008
```

Check it is up:

```bash
curl -H "Authorization: Bearer password" http://localhost:8008/
# {"status": true}
```

### Authentication

All routes except `/metrics` are protected by an HTTP bearer token. The accepted tokens come from (in order of precedence):

| Setting | Meaning |
|---------|---------|
| `PASSWORDFILE` | Path to a file with one accepted token per line |
| `PASSWORDS` | Semicolon-separated list of accepted tokens |
| *(default)* | A single token: `password` (development only) |

On the Spin image, `PASSWORDFILE` doubles as HTCondor's own `SEC_PASSWORD_FILE` (see `htcondor_configs/95-NERSC.conf`), so one shared secret is used for both condor's internal security and the API.

### Environment variables

| Variable | Default | Used by | Description |
|----------|---------|---------|-------------|
| `CONDOR_URL` | `http://localhost:8008` | client | Base URL of the htcondor-rest server |
| `CONDOR_PASS` | `password` | client | Bearer token for the server |
| `PASSWORDFILE` | – | server | File of accepted API tokens (one per line) |
| `PASSWORDS` | – | server | Semicolon-separated accepted API tokens |
| `METRICS_INTERVAL` | `60` | server | Seconds between metrics refreshes |
| `CONDOR_PORT` | `9000` | Spin config | HTCondor shared port inside the container |
| `USER` | – | Spin config | NERSC username; used for `MASTER_NAME`/`SCHEDD_NAME`/`UID_DOMAIN` |
| `HOSTNAME` | – | Spin config | Set automatically by Kubernetes to the pod hostname |
| `HTCONDOR_WORKER` | – | `pre-exec.sh` | If `0`/`false`, drop the `NEGOTIATOR`/`SCHEDD` daemons |
| `HTCONDOR_PORT` | – | `pre-exec.sh` | Override the collector port |

## API reference

Every endpoint (except `/metrics`) requires `Authorization: Bearer <token>`.

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check, returns `{"status": true}` |

### Queue (`condor_q`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/condor_q` | Query the job queue. Query params: `constraint`, `projection` (comma-separated), `limit` (default `-1` = all) |
| GET | `/condor_q/{job_id}` | Get a single job by cluster ID (404 if absent) |
| GET | `/condor_q_user` | User ads (`queryUserAds`) |
| GET | `/condor_q_project` | Project ads (`queryProjectAds`) |

### History (`condor_history`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/condor_history` | Job history. Params: `constraint`, `projection`, `match`, `since` |
| GET | `/condor_history/{job_id}` | Single history entry by cluster ID (404 if absent) |
| GET | `/condor_epoch_history` | Job epoch history |
| GET | `/condor_daemon_history` | Daemon history |

### Submission

| Method | Path | Description |
|--------|------|-------------|
| POST | `/condor_submit` | Submit a job from a JSON body of structured attributes (see models). `count` defaults to 1; `spool` holds the job for later input upload |
| POST | `/condor_submit_file` | Submit a job described by raw `condor_submit`-language text (full submit language supported, including `queue` statements). Body: `{ "submit_text": "...", "count": 0, "spool": false }` |
| POST | `/condor_spool` | Upload input files for the most recent `spool=true` submit |
| POST | `/condor_retrieve` | Retrieve output files. Body: `{ "job_ids": [...] }` or `{ "constraint": "..." }` |

Submit responses look like:

```json
{
  "cluster": 123,
  "clusterad": { ... },
  "first_proc": 0,
  "num_procs": 1,
  "submit_script": "..."
}
```

### Job actions

`condor_hold`, `condor_release`, `condor_suspend`, `condor_continue`, `condor_rm`, `condor_rmx`, `condor_vacate`, `condor_vacate_fast`. Each has two routes:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/condor_{action}/{job_id}` | Act on one job |
| POST | `/condor_{action}` | Act on jobs. Body: `{ "job_ids": [...], "constraint": "...", "reason": "..." }` |

There is also a legacy `DELETE /condor_rm/{job_id}`.

### Editing and administration

| Method | Path | Description |
|--------|------|-------------|
| POST | `/condor_edit` | Edit a job attribute. Body: `{ "job_ids" \| "constraint", "attr", "value" }` |
| POST | `/condor_reschedule` | Ask the schedd to renegotiate |
| POST | `/condor_export_jobs` | Export jobs. Body: `{ "job_ids" \| "constraint", "export_dir", "new_spool_dir" }` |
| POST | `/condor_import_exported_job_results` | Import results. Body: `{ "import_dir": "..." }` |
| POST | `/condor_unexport_jobs` | Unexport jobs |
| POST | `/condor_refresh_gsi_proxy` | Refresh a job's GSI proxy. Body: `{ "cluster", "proc", "proxy_filename", "lifetime" }` |
| GET | `/condor_claims` | Claimed-slot ClassAds from the schedd |

### One-click university (OCU) claims

`POST /condor_create_ocu`, `POST /condor_remove_ocu`, `POST /condor_query_ocu`, each with a body `{ "request": { ...ClassAd... } }`.

### Accounting records

User records: `add_user_rec`, `enable_user_rec`, `disable_user_rec`, `remove_user_rec`, `update_user_rec`.
Project records: `add_project_rec`, `enable_project_rec`, `disable_project_rec`, `remove_project_rec`, `update_project_rec`.

All are `POST /condor_{route}` with `{ "spec" | "constraint", "reason" }` (updates take `{ "ads": [...] }`).

### Collector / status

| Method | Path | Description |
|--------|------|-------------|
| GET | `/condor_status` | Query the collector. Params: `ad_type` (any, startd, slot, schedd, ...), `constraint`, `projection` |
| GET | `/condor_status/{name}` | A single ad by name (404 if absent) |
| GET | `/condor_nodes` | All machine (`MyType == "Machine"`) ads |
| GET | `/condor_locate/{daemon_type}` | Locate a daemon (`schedd`, `collector`, `negotiator`, ...) |
| GET | `/condor_locate_all/{daemon_type}` | Locate all daemons of a type |
| GET | `/condor_direct_query/{daemon_type}` | Bypass the collector and query a daemon directly |
| POST | `/condor_advertise` | Advertise ClassAds. Body: `{ "ads": [...], "command": "UPDATE_AD_GENERIC", "use_tcp": true }` |

### Configuration and negotiator

| Method | Path | Description |
|--------|------|-------------|
| GET | `/condor_config` | All `htcondor.param` values |
| GET | `/condor_config/{attribute}` | A single config attribute (404 if undefined) |
| GET | `/condor_userprio` | Negotiator user priorities |
| GET | `/condor_userprio/{user}` | Resource usage for one user |

### Metrics

`GET /metrics` is **public** (no auth) and exposes Prometheus-formatted aggregate counts:

- `htcondor_metrics_up` / `htcondor_metrics_last_scrape_seconds`
- `htcondor_queue_jobs{status="idle|running|held|..."}`
- `htcondor_history_jobs{result="completed|failed",window="all|1h|24h|7d|30d"}`

The metrics are cached in a background thread and refreshed every `METRICS_INTERVAL` seconds.

An OpenAPI/Swagger UI is served by FastAPI at `/docs`.

## Using the Python client

```python
from htcondor_rest import CondorClient

with CondorClient(base_url="http://localhost:8008", token="password") as condor:
    # submit a job from a structured dict
    result = condor.submit(
        {
            "executable": "/usr/bin/echo",
            "arguments": "Hello World",
            "count": 1,
            "output": "/tmp/out",
            "request_cpus": "1",
            "request_memory": "1",
            "request_disk": "1",
        }
    )
    cluster = result["cluster"]

    # or submit raw condor_submit text
    result = condor.submit_file("executable = /bin/echo\nqueue 3\n")

    # query
    queue = condor.get_queue(constraint="Owner == \"someone\"", projection="ClusterId,JobStatus")
    job = condor.get_queue(job_id=cluster)
    history = condor.get_history()
    status = condor.get_status(ad_type="startd")

    # act on jobs
    condor.hold(job_ids=[f"{cluster}.0"], reason="maintenance")
    condor.release(constraint="Owner == \"someone\"")
    condor.remove(job_ids=[f"{cluster}.0"])
    condor.edit(attr="JobPrio", value="5", job_ids=[str(cluster)])
    condor.reschedule()

    # metrics
    metrics_text = condor.get_metrics()
```

`CondorClient` reads `CONDOR_URL` and `CONDOR_PASS` from the environment when no arguments are given. Non-2xx responses raise `httpx.HTTPStatusError`. There is also `tests/test.py`, a small working example.

## Docker images

Two images are built from this repo (see `.github/workflows/build-docker.yml`).

### `Dockerfile` — full pool

Based on `htcondor/mini:25.7.2-el9`. Runs a complete HTCondor pool under `supervisord` (`condor_master`, `condor_restd`, and the REST app). Configure worker/manager roles via `HTCONDOR_WORKER`/`HTCONDOR_PORT` (see `htcondor_configs/pre-exec.sh`).

### `spin.Dockerfile` — mini pool for Spin@NERSC

A single container that runs `condor_master` (MASTER, COLLECTOR, NEGOTIATOR, SCHEDD, SHARED_PORT) **and** the REST server together via `htcondor_configs/start.sh`. The REST server listens on port `8008`; HTCondor uses shared port `CONDOR_PORT` (default `9000`).

Key properties:

- Runs as an unprivileged user (defaults in the Dockerfile: user `tylern`, UID/GID `95745` — **override with `--build-arg USER/UID/GID`** for your NERSC account).
- Uses `/scratch` for `LOCAL_DIR` and `/logs/condor` for HTCondor's security password and spool/log dirs.
- Reads config from `/data/htcondorlogs/95-NERSC.conf` (via `CONDOR_CONFIG`).

## Deploying on Spin@NERSC

Spin is NERSC's container platform for hosting science gateways and API services. See the [Spin documentation](https://docs.nersc.gov/services/spin/) — you need an active NERSC account, access to Spin (via the SpinUp workshop or approved self-guided training), and a namespace in your project.

### 1. Build and push the image

The image must run on Linux/amd64. From this repo:

```bash
docker build \
  --platform linux/amd64 \
  --build-arg USER=<your-nersc-username> \
  --build-arg UID=<your-nersc-uid> \
  --build-arg GID=<your-nersc-gid> \
  -f spin.Dockerfile \
  -t registry.nersc.gov/<project>/htcondor-rest:<tag> .
```

(Your NERSC UID/GID and project name come from `iris`/`id`. CI builds this image automatically as `ghcr.io/<owner>/<repo>:spin-<branch>` — you can push from a GitHub release instead.)

Log into NERSC's Harbor registry and push:

```bash
docker login registry.nersc.gov   # use your NERSC credentials
docker push registry.nersc.gov/<project>/htcondor-rest:<tag>
```

### 2. Create the workload

1. Log into [Rancher](https://rancher2.spin.nersc.gov/) and select your **development** or **production** cluster.
2. Open your project → **Workloads** → **Create** → **Deployment**.
3. Name it (e.g. `htcondor-rest`) and set the **Container Image** to `registry.nersc.gov/<project>/htcondor-rest:<tag>`.
4. Leave the **Container Name** as `container-0`.

### 3. Security context (required)

Spin drops all Linux capabilities by default, which would break HTCondor. Under the container's **Security Context**:

- **Drop Capabilities**: add `ALL`
- **Add Capabilities**: add `CHOWN`, `KILL`, `SETGID`, `SETUID`, `DAC_OVERRIDE`, and `FOWNER`
- Set the **Run As** user/group to your NERSC **UID/GID** if you mount a NERSC Global File System (NGF) volume (Spin only allows `NET_BIND_SERVICE` in that case — see the [Spin storage docs](https://docs.nersc.gov/services/spin/storage/)).

### 4. Environment variables

| Variable | Value |
|----------|-------|
| `USER` | your NERSC username (drives `MASTER_NAME`, `SCHEDD_NAME`, `UID_DOMAIN`). `start.sh` has a hardcoded `USER=tylren` that is never exported, so set this explicitly or the condor config's `$ENV(USER)` will be empty |
| `HOSTNAME` | leave unset — Kubernetes sets the pod hostname automatically |
| `CONDOR_PORT` | `9000` |
| `PASSWORDS` | semicolon-separated API bearer tokens for the REST server |
| `PASSWORDFILE` | **filename only**, e.g. `condor_pass` — used by HTCondor's `SEC_PASSWORD_FILE` |
| `METRICS_INTERVAL` | `60` |

> **Path quirk:** the REST server resolves `PASSWORDFILE` relative to its working directory (`/app`), while `95-NERSC.conf` resolves it under `/logs/condor/`. They are intentionally different secrets, so use `PASSWORDS` for the API token and `PASSWORDFILE` (a bare filename) for HTCondor's internal pool password. If you set `PASSWORDFILE` to a full path, condor would try to create `/logs/condor/<that-path>`, which breaks the config.

`start.sh` copies nothing onto the mounted volumes, so also make sure the `/logs/condor`, `/scratch`, and `/data/htcondorlogs` paths exist and are writable:

- Create a secret holding your bearer token/password and mount it, or
- Mount an NGF volume, then create `/logs/condor/<PASSWORDFILE>` with the token text and make `/scratch` and `/data/htcondorlogs` writable.

### 5. Add storage (optional)

Attach NGF volumes via the **Storage** tab if you want jobs and logs to survive pod restarts. Point the workload's volumes at:

- `/scratch` — HTCondor `LOCAL_DIR` (spool, logs)
- `/logs/condor` — security password and log directory
- `/data/htcondorlogs` — the config directory (`CONDOR_CONFIG`)

### 6. Expose the app

1. Under the container's **Ports**, add a **ClusterIP** port for the REST API:
   - Service type: Cluster IP
   - Name: `http` (any name)
   - Port: `8008`
   - Protocol: TCP
2. **Service Discovery → Ingresses → Create**, name it `htcondor-rest`, and set:
   - **Requested Host**: `htcondor-rest.<namespace>.<environment>.svc.spin.nersc.org`
   - **Path**: Prefix `/`, target service = your workload, port 8008
   - **Ingress Class**: `nginx`
3. Wait 1–5 minutes for DNS, then test:

```bash
curl -H "Authorization: Bearer <token>" \
  http://htcondor-rest.<namespace>.<environment>.svc.spin.nersc.org/condor_q
```

For HTTPS, set up a custom DNS name (CNAME to the `.svc.spin.nersc.org` hostname), add a TLS certificate secret, and attach it to the ingress.

### 7. Verify

In Rancher, open the pod → **⋮** → **Execute shell**:

```bash
condor_status          # should show the local mini pool
condor_q               # empty queue
curl -H "Authorization: Bearer <token>" http://localhost:8008/  # {"status": true}
```

Then query the queue from your laptop with the Python client pointed at the ingress URL:

```bash
CONDOR_URL=http://htcondor-rest.<namespace>.<environment>.svc.spin.nersc.org \
CONDOR_PASS=<token> \
python -c "from htcondor_rest import CondorClient; c = CondorClient(); print(c.get_queue())"
```

## Development and testing

The tests use a dummy `htcondor2` module so they run without HTCondor, but `htcondor` only ships Linux wheels, so the suite must run on Linux. `scripts/run-tests.sh` builds a small image (`Dockerfile.test`) with the dependencies pre-installed and runs pytest inside it — Docker layer caching keeps repeat runs fast, so this works well even on macOS:

```bash
scripts/run-tests.sh                # full suite
scripts/run-tests.sh -k submit      # only tests matching "submit"
scripts/run-tests.sh tests/test_auth.py
```

Pass any pytest arguments straight through. Overridables: `TEST_IMAGE`, `TEST_DOCKERFILE`, `TEST_PYTHON_TAG`. The wheel also has an `aarch64` build, so Apple Silicon runs natively inside the container.

Or on a Linux machine:

```bash
uv sync --all-extras --dev
uv run pytest
```

`uv.lock` is intentionally not committed. The deployable artifacts are Docker images, and dependency resolution happens inside the image build, so images stay reproducible without a lockfile (and without lockfile merge conflicts). Local and CI installs resolve fresh against `pyproject.toml`, so keep the `>=` constraints current.

### Pre-commit hooks

A set of pre-commit hooks keeps the repo tidy. Run `pre-commit install` once, and the hooks run on every commit (or manually with `pre-commit run --all-files`):

- **ruff** (`ruff`, `ruff-format`): Python linting (with autofix) and formatting.
- **pre-commit-hooks**: whitespace/EOF hygiene, YAML/TOML/JSON validation, shebang checks, merge-conflict and private-key detection.
- **hadolint**: lints the Dockerfiles.
- **actionlint**: lints the GitHub Actions workflows.
- **typos**: catches typos (HTCondor daemon names like `startd` are whitelisted in `pyproject.toml`).

The API and client tests are in `tests/test_api.py` and `tests/test_client.py`; CI runs them on Python 3.13 and 3.14 via `.github/workflows/pytest.yml`.

## Notes and known quirks

- The `spool=True` submit flow keeps the last submit result in process memory, so `/condor_spool` must be called against the same server process that performed the submit (fine with a single gunicorn worker, which the provided `start.sh`/`submit_rest.sh` use).
- `/metrics` is intentionally public — it only exposes aggregate job counts.
- On the Spin image, keep the API token (`PASSWORDS`) and HTCondor's pool password (`PASSWORDFILE`) separate, and protect both. They are read differently by the REST server and by `95-NERSC.conf` (see the path quirk above).
