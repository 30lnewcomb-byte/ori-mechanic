from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass(frozen=True)
class BrowserEvent:
    event: str
    detail: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class BrowserMonitor:
    def __init__(self) -> None:
        self.events: list[BrowserEvent] = []

    def record(self, event: str, detail: str = "") -> BrowserEvent:
        item = BrowserEvent(event=event, detail=detail)
        self.events.append(item)
        return item

    def recent(self, limit: int = 100) -> list[BrowserEvent]:
        return self.events[-limit:]
