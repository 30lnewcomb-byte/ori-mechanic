from collections import deque
from threading import Lock

from mechanic.heartbeat import WakeNotice

class WakeEventBus:
    """Small in-process wake queue. A production deployment can back this with a durable queue."""

    def __init__(self) -> None:
        self._queue: deque[WakeNotice] = deque()
        self._lock = Lock()

    def publish(self, notice: WakeNotice) -> None:
        with self._lock:
            self._queue.append(notice)

    def drain(self) -> list[WakeNotice]:
        with self._lock:
            notices = list(self._queue)
            self._queue.clear()
            return notices

    def pending(self) -> int:
        with self._lock:
            return len(self._queue)
