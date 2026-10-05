import os
import shlex
import subprocess
import time

from fastapi import FastAPI
from sandbox.models import JobRequest, JobResult
from sandbox.policy import validate_command

app = FastAPI(title="Ori Mechanic Sandbox", version="0.1.0")

WORKSPACE = os.environ.get("SANDBOX_WORKSPACE", "/workspace")

@app.get("/health")
def health():
    return {"service": "ori-mechanic-sandbox", "status": "online", "version": "0.1.0"}

@app.post("/v1/jobs", response_model=JobResult)
def run_job(job: JobRequest):
    allowed, reason = validate_command(job.command)
    if not allowed:
        return JobResult(
            status="rejected",
            duration_ms=0,
            reason=reason,
        )

    started = time.monotonic()
    try:
        result = subprocess.run(
            shlex.split(job.command),
            cwd=WORKSPACE,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=job.timeout_seconds,
            env={
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "HOME": "/tmp",
                "PYTHONUNBUFFERED": "1",
            },
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        return JobResult(
            status="completed" if result.returncode == 0 else "failed",
            exit_code=result.returncode,
            stdout=result.stdout[-20000:],
            stderr=result.stderr[-20000:],
            duration_ms=duration_ms,
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        return JobResult(
            status="timeout",
            duration_ms=duration_ms,
            stdout=(exc.stdout or "")[-20000:],
            stderr=(exc.stderr or "")[-20000:],
            reason="execution timeout",
        )
