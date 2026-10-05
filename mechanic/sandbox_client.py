import os
import urllib.error
import urllib.request
import json

from .models import ExecutionRequest, ExecutionResult

class SandboxAPIError(RuntimeError):
    pass

class SandboxAPIAdapter:
    """Authenticated API client; Mechanic never gets a shell into the sandbox."""
    name = "sandbox-api"

    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        self.base_url = (base_url or os.environ.get("SANDBOX_API_URL", "http://sandbox:8080")).rstrip("/")
        self.token = token or os.environ.get("SANDBOX_API_TOKEN", "")
        if not self.token:
            raise SandboxAPIError("SANDBOX_API_TOKEN is not configured")

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        payload = json.dumps({
            "command": request.command,
            "timeout_seconds": request.timeout_seconds,
            "network": False,
            "workspace": "/workspace",
        }).encode()
        req = urllib.request.Request(
            f"{self.base_url}/v1/jobs", data=payload,
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=request.timeout_seconds + 5) as response:
                return ExecutionResult.model_validate_json(response.read())
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            raise SandboxAPIError(f"sandbox API rejected request: HTTP {exc.code}: {body[:500]}") from exc
        except urllib.error.URLError as exc:
            raise SandboxAPIError("sandbox API is unavailable") from exc
