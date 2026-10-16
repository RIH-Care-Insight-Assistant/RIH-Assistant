"""In-memory token-bucket rate limiter (single process; documented limitation)."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable, Dict, Tuple


@dataclass(frozen=True)
class Limit:
    capacity: int       # burst size
    per_seconds: float  # time to refill the full bucket


DEFAULT_LIMITS: Dict[str, Limit] = {
    "chat": Limit(20, 60),       # 20 chat turns per minute per client
    "login": Limit(10, 300),     # 10 login attempts per 5 minutes per client
    "write": Limit(60, 60),      # other mutating calls
    "read": Limit(300, 60),
}


class RateLimiter:
    def __init__(self, limits: Dict[str, Limit] | None = None, *, max_keys: int = 10_000,
                 clock: Callable[[], float] = time.monotonic):
        self.limits = dict(limits or DEFAULT_LIMITS)
        self._buckets: "OrderedDict[Tuple[str, str], Tuple[float, float]]" = OrderedDict()
        self._lock = threading.Lock()
        self._max_keys = max_keys
        self._clock = clock

    def check(self, bucket: str, key: str) -> Tuple[bool, int]:
        """Consume one token. Returns (allowed, retry_after_seconds)."""
        limit = self.limits[bucket]
        rate = limit.capacity / limit.per_seconds
        now = self._clock()
        with self._lock:
            tokens, last = self._buckets.pop((bucket, key), (float(limit.capacity), now))
            tokens = min(float(limit.capacity), tokens + (now - last) * rate)
            allowed = tokens >= 1.0
            if allowed:
                tokens -= 1.0
            self._buckets[(bucket, key)] = (tokens, now)
            while len(self._buckets) > self._max_keys:
                self._buckets.popitem(last=False)
        retry = 0 if allowed else max(1, int((1.0 - tokens) / rate + 0.999))
        return allowed, retry
