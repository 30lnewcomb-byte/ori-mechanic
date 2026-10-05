import os
import shlex
import subprocess
import time

from fastapi import FastAPI
from sandbox.models import JobRequest, JobResult
from sandbox.policy import validate_command

app = FastAPI(title="Ori Mechanic Sandbox", version="0.2.0")
WORKSPACE = os.environ.get("SANDBOX_WORKSPACE", "/workspace")
MAX_OUTPUT = 20_000

@app.get("/health")
def health():
    return {"service": "ori-mechanic-sandbox", "status": "online", "version": "0.2.0"}

@app.post("/v1/jobs", response_model=JobResult)
def run_job(job: JobRequest):
    if job.network:
        return JobResult(status="rejected", duration_ms=0,
                         reason="network access is not available in the sandbox runtime")
    allowed, reason = validate_command(job.command)
    if not allowed:
        return JobResult(status="rejected", duration_ms=0, reason=reason)

    started = time.monotonic()
    try:
        result = subprocess.run(
            shlex.split(job.command),
            cwd=WORKSPACE,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=job.timeout_seconds,
            env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp",
                 "TMPDIR": "/tmp", "PYTHONUNBUFFERED": "1"},
        )
        return JobResult(
            status="completed" if result.returncode == 0 else "failed",
            exit_code=result.returncode,
            stdout=result.stdout[-MAX_OUTPUT:],
            stderr=result.stderr[-MAX_OUTPUT:],
            duration_ms=int((time.monotonic() - started) * 1000),
        )
    except subprocess.TimeoutExpired as exc:
        return JobResult(
            status="timeout",
            duration_ms=int((time.monotonic() - started) * 1000),
            stdout=str(exc.stdout or "")[-MAX_OUTPUT:],
            stderr=str(exc.stderr or "")[-MAX_OUTPUT:],
            reason="execution timeout",
        )
