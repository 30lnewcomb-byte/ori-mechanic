from pydantic import BaseModel, Field
from typing import Literal

class JobRequest(BaseModel):
    command: str = Field(min_length=1, max_length=2000)
    timeout_seconds: int = Field(default=30, ge=1, le=120)
    network: bool = False
    workspace: str = Field(default="/workspace", pattern=r"^/workspace$")

class JobResult(BaseModel):
    status: Literal["completed", "rejected", "timeout", "failed"]
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration_ms: int
    reason: str | None = None
