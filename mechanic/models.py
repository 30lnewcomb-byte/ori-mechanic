from enum import Enum
from pydantic import BaseModel, Field

class Autonomy(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"

class Incident(BaseModel):
    id: str
    source: str
    title: str
    description: str
    severity: str = "medium"

class Action(BaseModel):
    id: str
    incident_id: str
    action_type: str
    summary: str
    autonomy: Autonomy | None = None
    target: str | None = None
    reversible: bool = True

class Approval(BaseModel):
    id: str
    action_id: str
    status: str = "pending"
    requested_by: str = "mechanic"
    decision: str | None = None

class ExecutionRequest(BaseModel):
    action_id: str
    command: str = Field(min_length=1, max_length=2000)
    timeout_seconds: int = Field(default=30, ge=1, le=120)

class ExecutionResult(BaseModel):
    status: str
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0
    reason: str | None = None
