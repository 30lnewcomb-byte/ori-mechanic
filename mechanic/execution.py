from typing import Protocol
from .models import ExecutionRequest, ExecutionResult

class ExecutionAdapter(Protocol):
    name: str
    def execute(self, request: ExecutionRequest) -> ExecutionResult: ...

class SandboxAdapter:
    """Transport boundary for the isolated sandbox."""
    name = "sandbox"

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        raise RuntimeError("sandbox transport is not connected yet")
