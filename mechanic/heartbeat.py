from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

class MechanicState(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    WAKING = "waking"

@dataclass(frozen=True)
class WakeNotice:
    source: str
    reason: str
    priority: str = "normal"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class MechanicHeartbeat:
    state: MechanicState = MechanicState.IDLE
    last_activity: datetime | None = None
    last_wake: datetime | None = None
    wake_count: int = 0

    def go_idle(self) -> None:
        self.state = MechanicState.IDLE

    def wake(self, notice: WakeNotice) -> None:
        self.state = MechanicState.WAKING
        self.last_wake = notice.created_at
        self.last_activity = notice.created_at
        self.wake_count += 1

    def active(self) -> None:
        self.state = MechanicState.ACTIVE
        self.last_activity = datetime.now(timezone.utc)
