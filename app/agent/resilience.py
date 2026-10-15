"""Circuit breaker and bounded concurrency for optional model calls.

Addresses C1 deferral O9 for the planner path: at most `max_inflight` model calls run at
once (extra requests skip the model instead of queueing threads), and after
`failure_threshold` consecutive failures or timeouts the breaker opens for
`reset_after_s`, during which the deterministic planner is used without calling the model.
"""

from __future__ import annotations

import threading
import time
from typing import Callable


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_after_s: float = 30.0, max_inflight: int = 2,
                 clock: Callable[[], float] = time.monotonic):
        self.failure_threshold = failure_threshold
        self.reset_after_s = reset_after_s
        self._clock = clock
        self._lock = threading.Lock()
        self._failures = 0
        self._opened_at: float | None = None
        self._slots = threading.BoundedSemaphore(max_inflight)

    @property
    def state(self) -> str:
        with self._lock:
            if self._opened_at is None:
                return "closed"
            if self._clock() - self._opened_at >= self.reset_after_s:
                return "half_open"
            return "open"

    def acquire(self) -> bool:
        """True if a model call may start now. The caller must call `release()` afterwards."""
        if self.state == "open":
            return False
        return self._slots.acquire(blocking=False)

    def release(self) -> None:
        self._slots.release()

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._opened_at = self._clock()
