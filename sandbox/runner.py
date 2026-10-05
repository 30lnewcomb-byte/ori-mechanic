import hmac
import os
import shlex
import subprocess
import time

from fastapi import Depends, FastAPI, Header, HTTPException
from sandbox.models import JobRequest, JobResult
from sandbox.policy import validate_command

app = FastAPI(title="Ori Mechanic Sandbox", version="0.3.0")
WORKSPACE = "/workspace"
MAX_OUTPUT = 20_000
API_TOKEN = os.environ.get("SANDBOX_API_TOKEN", "")


def require_api_token(authorization: str | None = Header(default=None)) -> None:
    if not API_TOKEN:
        raise HTTPException(status_code=503, detail="sandbox API authentication is not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="authentication required")
    supplied = authorization[7:]
    if not hmac.compare_digest(supplied, API_TOKEN):
        raise HTTPException(status_code=403, detail="invalid sandbox credential")

@app.get("/health")
def health():
    return {"service": "ori-mechanic-sandbox", "status": "online", "version": "0.3.0"}

@app.get("/v1/capabilities")
def capabilities(_: None = Depends(require_api_token)):
    return {"execution": True, "network": False, "workspace": "/workspace", "credential_access": False}

@app.post("/v1/jobs", response_model=JobResult)
def run_job(job: JobRequest, _: None = Depends(require_api_token)):
    if job.network:
        return JobResult(status="rejected", duration_ms=0,
                         reason="network access is permanently disabled in the sandbox")
    allowed, reason = validate_command(job.command)
    if not allowed:
        return JobResult(status="rejected", duration_ms=0, reason=reason)

    started = time.monotonic()
    try:
        result = subprocess.run(
            shlex.split(job.command), cwd=WORKSPACE, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=job.timeout_seconds,
            env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp",
                 "TMPDIR": "/tmp", "PYTHONUNBUFFERED": "1"},
        )
        return JobResult(
            status="completed" if result.returncode == 0 else "failed",
            exit_code=result.returncode, stdout=result.stdout[-MAX_OUTPUT:],
            stderr=result.stderr[-MAX_OUTPUT:],
            duration_ms=int((time.monotonic() - started) * 1000),
        )
    except subprocess.TimeoutExpired as exc:
        return JobResult(status="timeout",
                         duration_ms=int((time.monotonic() - started) * 1000),
                         stdout=str(exc.stdout or "")[-MAX_OUTPUT:],
                         stderr=str(exc.stderr or "")[-MAX_OUTPUT:],
                         reason="execution timeout")
