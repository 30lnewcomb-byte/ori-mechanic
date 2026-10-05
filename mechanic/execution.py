from typing import Protocol
from .models import ExecutionRequest, ExecutionResult
from .sandbox_client import SandboxAPIAdapter

class ExecutionAdapter(Protocol):
    name: str
    def execute(self, request: ExecutionRequest) -> ExecutionResult: ...

class SandboxAdapter:
    """Mechanic execution boundary: API only, never direct process execution."""
    name = "sandbox-api"

    def __init__(self) -> None:
        self._client = SandboxAPIAdapter()

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        return self._client.execute(request)
