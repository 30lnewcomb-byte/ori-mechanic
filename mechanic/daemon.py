import time

from mechanic.event_bus import WakeEventBus
from mechanic.heartbeat import MechanicHeartbeat, MechanicState

class MechanicDaemon:
    """Always-on shell for Mechanic. It stays cheap while idle and wakes on notices."""

    def __init__(self, bus: WakeEventBus, heartbeat: MechanicHeartbeat | None = None) -> None:
        self.bus = bus
        self.heartbeat = heartbeat or MechanicHeartbeat()
        self.running = False

    def run_once(self) -> list[object]:
        notices = self.bus.drain()
        if not notices:
            self.heartbeat.go_idle()
            return []

        for notice in notices:
            self.heartbeat.wake(notice)
            # The decision engine consumes the notice here in the next layer.
            self.heartbeat.active()
        return notices

    def run_forever(self, poll_seconds: float = 1.0) -> None:
        self.running = True
        while self.running:
            self.run_once()
            time.sleep(poll_seconds)

    def stop(self) -> None:
        self.running = False
