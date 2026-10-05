# Ori Mechanic

Ori Mechanic is an independent infrastructure recovery system for the Ori ecosystem.

## Sandbox

The sandbox is a deliberately isolated execution environment for Mechanic repair jobs. It is designed to be portable across cloud providers and never depend on Ori itself for execution.

### Principles

- No host filesystem access
- No privileged containers
- Network disabled by default
- Explicit workspace mounted for each job
- Resource and execution limits
- Allowlisted commands only
- Every execution produces a structured result
- Destructive or infrastructure-changing actions remain outside the sandbox

## Layout

```
sandbox/
  runner.py       HTTP API for creating and running jobs
  policy.py       execution policy and command allowlist
  models.py       request/result models
  Dockerfile      isolated runtime image
  requirements.txt runtime dependencies
```

The sandbox is an execution boundary, not the Mechanic brain. Mechanic decides what should happen; the sandbox provides a constrained place to perform approved work.
