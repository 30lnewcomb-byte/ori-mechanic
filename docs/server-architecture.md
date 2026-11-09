# Ori Mechanic server architecture

## Deployment shape

Ori Mechanic is a provider-independent control plane. Deploy the coordinator/API
as a container, with browser and sandbox workers as separate services. The
browser worker is not the coordinator, and the sandbox is not the Mechanic brain.

- Coordinator/API: authenticates repair requests, creates durable jobs, checks
  policy and approval state, and dispatches eligible work.
- Job persistence: stores job state, attempts, timestamps, results, and worker
  leases. A worker must hold a current lease to complete a job.
- Browser worker: isolated Chromium/Playwright with exact host allowlists and
  short-lived non-persistent contexts.
- Sandbox worker: isolated command execution, network disabled by default,
  strict command allowlists, and resource limits.
- Inference adapter: calls the configured primary model endpoint. It cannot
  grant capabilities or approvals and does not own job state.

## Model failover: warm standby

The primary inference endpoint remains the normal route. Ori Small is a separate,
independently health-checked warm standby endpoint. The inference adapter should:

1. Apply a short timeout and bounded retry to the primary endpoint.
2. Mark the primary unavailable only after a defined failure threshold.
3. Route eligible inference requests to Ori Small while primary is unavailable.
4. Record provider/model, latency, and fallback reason for each response.
5. Probe the primary and return traffic only after configurable successful checks.
6. Keep policy, approvals, persistence, browser access, and sandbox execution
   independent of either model endpoint.

Failover must never expand permissions or silently approve an action. If both
models are unavailable, jobs remain persisted and retryable; the control plane
returns an explicit unavailable state.

## Persistence and hosting

Back4App remains a candidate for managed persistence, not a place to run
Chromium. The job-store interface should remain provider-neutral. The SQLite
implementation is suitable for local development and a single-instance host
with a persistent disk. Multi-instance production needs a shared transactional
database adapter.

The host must support long-running Docker containers, persistent storage,
private service-to-service networking, secrets, health checks, and bounded
resource use. Browser and sandbox services should not be exposed directly to
the public internet. Oracle Cloud is not a required dependency.

## Current implementation boundary

The first durable queue primitive is mechanic/job_store.py. It provides atomic
claims, expiring worker leases, bounded retries, and persisted results. It is
not yet a complete public coordinator API or multi-worker dispatcher. Those
pieces must be built and validated before production deployment.
