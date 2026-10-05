from datetime import datetime, timezone
from typing import Any

class AuditLog:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(self, event: str, **details: Any) -> None:
        self.events.append({"timestamp": datetime.now(timezone.utc).isoformat(), "event": event, "details": details})
