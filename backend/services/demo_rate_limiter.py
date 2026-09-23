"""Small process-local guard for the anonymous portfolio-demo endpoint.

The limit is intentionally a best-effort per-process control. Deployments with
multiple workers or changing proxy addresses need an edge or shared limiter for
globally consistent enforcement. X-Forwarded-For is used only when the hosting
environment is explicitly configured as trusted.
"""

from __future__ import annotations

from collections import defaultdict
from collections import deque
from ipaddress import ip_address
from threading import RLock
from time import monotonic


class ProcessLocalDemoRateLimiter:
    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = RLock()

    def allow(self, client_host: str | None, limit: int, window_seconds: int) -> bool:
        """Allow at most ``limit`` requests per observed connection host/window."""
        identity = client_host or "unknown-client"
        now = monotonic()
        with self._lock:
            timestamps = self._requests[identity]
            cutoff = now - max(window_seconds, 1)
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            if len(timestamps) >= max(limit, 1):
                return False
            timestamps.append(now)
            return True

    def reset(self) -> None:
        """Clear observations for isolated tests or a deliberate local reset."""
        with self._lock:
            self._requests.clear()


demo_rate_limiter = ProcessLocalDemoRateLimiter()


def select_demo_client_host(
    socket_host: str | None,
    forwarded_for: str | None,
    trust_proxy_headers: bool,
) -> str | None:
    """Choose a limiter identity without trusting forwarded headers by default."""
    if trust_proxy_headers and forwarded_for:
        for candidate in forwarded_for.split(","):
            try:
                return str(ip_address(candidate.strip()))
            except ValueError:
                continue
    return socket_host
