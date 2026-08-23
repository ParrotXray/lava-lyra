import random
import socket
import time
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from itertools import zip_longest
from timeit import default_timer as timer
from typing import Any, NamedTuple, override

from .enums import RouteIPType, RouteStrategy

__all__ = (
    "ConnectionQualityTracker",
    "ExponentialBackoff",
    "FailingIPBlock",
    "LavalinkVersion",
    "NodeHealthMonitor",
    "NodeStats",
    "Ping",
    "RouteStats",
    "voice_field",
)


class ExponentialBackoff:
    """
    The MIT License (MIT)
    Copyright (c) 2015-present Rapptz
    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:
    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
    """

    def __init__(self, base: int = 1, *, integral: bool = False) -> None:
        self._base = base

        self._exp = 0
        self._max = 10
        self._reset_time = base * 2**11
        self._last_invocation = time.monotonic()

        rand = random.Random()
        rand.seed()

        self._randfunc = rand.randrange if integral else rand.uniform

    def delay(self) -> float:
        invocation = time.monotonic()
        interval = invocation - self._last_invocation
        self._last_invocation = invocation

        if interval > self._reset_time:
            self._exp = 0

        self._exp = min(self._exp + 1, self._max)
        return self._randfunc(0, self._base * 2**self._exp)


class NodeStats:
    """The base class for the node stats object.
    Gives critical information on the node, which is updated every 60 seconds on Lavalink or every 30 seconds on NodeLink.
    """

    __slots__ = (
        "allocated",
        "cpu_cores",
        "cpu_process_load",
        "cpu_system_load",
        "free",
        "players_active",
        "players_total",
        "reservable",
        "uptime",
        "used",
    )

    def __init__(self, data: dict[str, Any]) -> None:
        memory: dict[str, Any] = data.get("memory") or {}
        self.used = memory.get("used")
        self.free = memory.get("free")
        self.reservable = memory.get("reservable")
        self.allocated = memory.get("allocated")

        cpu: dict[str, Any] = data.get("cpu") or {}
        self.cpu_cores = cpu.get("cores")
        self.cpu_system_load = cpu.get("systemLoad")
        self.cpu_process_load = cpu.get("lavalinkLoad", cpu.get("nodelinkLoad"))

        self.players_active = data.get("playingPlayers") or 0
        self.players_total = data.get("players") or 0
        self.uptime = data.get("uptime")

    def __repr__(self) -> str:
        return f"<Lyra.NodeStats total_players={self.players_total!r} playing_active={self.players_active!r}>"


class FailingIPBlock:
    """
    The base class for the failing IP block object from the route planner stats.
    Gives critical information about any failing addresses on the block
    and the time they failed.
    """

    __slots__ = ("address", "failing_time")

    def __init__(self, data: dict[str, Any]) -> None:
        self.address = data.get("failingAddress")
        self.failing_time = datetime.fromtimestamp(
            float(data.get("failingTimestamp") or 0) / 1000,
            tz=UTC,
        )

    def __repr__(self) -> str:
        return f"<Lyra.FailingIPBlock address={self.address} failing_time={self.failing_time}>"


class RouteStats:
    """
    The base class for the route planner stats object.
    Gives critical information about the route planner strategy on the node.
    """

    __slots__ = (
        "address_index",
        "block_index",
        "failing_addresses",
        "ip_block_size",
        "ip_block_type",
        "strategy",
    )

    def __init__(self, data: dict[str, Any]) -> None:
        strategy_value = data.get("class")
        try:
            self.strategy: RouteStrategy | None = (
                RouteStrategy(strategy_value) if strategy_value is not None else None
            )
        except ValueError:
            self.strategy = None

        details: dict[str, Any] = data.get("details") or {}

        ip_block: dict[str, Any] = details.get("ipBlock") or {}
        ip_block_type_value = ip_block.get("type")
        try:
            self.ip_block_type: RouteIPType | None = (
                RouteIPType(ip_block_type_value) if ip_block_type_value is not None else None
            )
        except ValueError:
            self.ip_block_type = None
        self.ip_block_size = ip_block.get("size")
        self.failing_addresses = [
            FailingIPBlock(
                data,
            )
            for data in details.get("failingAddresses", [])
        ]

        self.block_index = details.get("blockIndex")
        self.address_index = details.get("currentAddressIndex")

    def __repr__(self) -> str:
        return f"<Lyra.RouteStats route_strategy={self.strategy!r} failing_addresses={len(self.failing_addresses)}>"


class Ping:
    # Thanks to https://github.com/zhengxiaowai/tcping for the nice ping impl
    def __init__(self, host: str, port: int, timeout: int = 5) -> None:
        self.timer = self.Timer()

        self._host = host
        self._port = port
        self._timeout = timeout

    class Socket:
        def __init__(self, family: int, type_: int, timeout: float | None) -> None:
            s = socket.socket(family, type_)
            s.settimeout(timeout)
            self._s = s

        def connect(self, host: str, port: int) -> None:
            self._s.connect((host, port))

        def shutdown(self) -> None:
            self._s.shutdown(socket.SHUT_RD)

        def close(self) -> None:
            self._s.close()

    class Timer:
        def __init__(self) -> None:
            self._start: float = 0.0
            self._stop: float = 0.0

        def start(self) -> None:
            self._start = timer()

        def stop(self) -> None:
            self._stop = timer()

        def cost(self, funcs: Iterable[Callable[..., Any]], args: Any) -> float:
            self.start()
            for func, arg in zip_longest(funcs, args):
                if arg:
                    func(*arg)
                else:
                    func()

            self.stop()
            return self._stop - self._start

    def _create_socket(self, family: int, type_: int) -> Socket:
        return self.Socket(family, type_, self._timeout)

    def get_ping(self) -> float:
        """
        Get ping latency in milliseconds.
        Returns -1.0 if the connection fails (node is unreachable).
        """
        s = self._create_socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            cost_time = self.timer.cost(
                (s.connect, s.shutdown),
                ((self._host, self._port), None),
            )
            s_runtime = 1000 * (cost_time)
            s.close()
            return s_runtime
        except (TimeoutError, ConnectionRefusedError, OSError):
            # Node is unreachable or offline
            try:
                s.close()
            except Exception:
                pass
            return -1.0


class LavalinkVersion(NamedTuple):
    major: int
    minor: int
    fix: int

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LavalinkVersion):
            return NotImplemented

        return (
            (self.major == other.major) and (self.minor == other.minor) and (self.fix == other.fix)
        )

    @override
    def __lt__(self, other: object) -> bool:
        if not isinstance(other, LavalinkVersion):
            return NotImplemented

        return (self.major, self.minor, self.fix) < (other.major, other.minor, other.fix)

    @override
    def __gt__(self, other: object) -> bool:
        if not isinstance(other, LavalinkVersion):
            return NotImplemented

        return (self.major, self.minor, self.fix) > (other.major, other.minor, other.fix)

    @override
    def __ge__(self, other: object) -> bool:
        if not isinstance(other, LavalinkVersion):
            return NotImplemented

        return (self > other) or (self == other)


class ConnectionQualityTracker:
    """
    Tracks connection quality metrics for a node to help make better
    failover and load balancing decisions.
    """

    __slots__ = (
        "_connection_start_time",
        "_consecutive_failures",
        "_failure_start_time",
        "_latency_samples",
        "_max_latency_samples",
        "_reconnection_count",
        "_total_downtime",
    )

    def __init__(self, max_latency_samples: int = 10) -> None:
        self._reconnection_count: int = 0
        self._connection_start_time: float = time.time()
        self._total_downtime: float = 0.0
        self._latency_samples: list[float] = []
        self._max_latency_samples: int = max_latency_samples
        self._consecutive_failures: int = 0
        self._failure_start_time: float = 0.0

    def record_reconnection(self) -> None:
        """Record a reconnection event."""
        current_time = time.time()
        if self._failure_start_time > 0:
            self._total_downtime += current_time - self._failure_start_time
            self._failure_start_time = 0.0

        self._reconnection_count += 1

    def record_connection_success(self) -> None:
        """Record a successful connection."""
        self._consecutive_failures = 0
        self._failure_start_time = 0.0
        self._connection_start_time = time.time()

    def record_connection_failure(self) -> None:
        """Record a connection failure."""
        if self._consecutive_failures == 0:
            self._failure_start_time = time.time()
        self._consecutive_failures += 1

    def record_latency(self, latency: float) -> None:
        """Record a latency sample."""
        if latency >= 0:  # Only record valid latencies
            self._latency_samples.append(latency)
            if len(self._latency_samples) > self._max_latency_samples:
                self._latency_samples.pop(0)

    @property
    def average_latency(self) -> float:
        """Get average latency from recent samples."""
        if not self._latency_samples:
            return -1.0
        return sum(self._latency_samples) / len(self._latency_samples)

    @property
    def uptime_percentage(self) -> float:
        """Calculate uptime percentage."""
        total_time = time.time() - self._connection_start_time
        if total_time <= 0:
            return 100.0
        uptime = total_time - self._total_downtime
        return (uptime / total_time) * 100.0

    @property
    def reconnection_count(self) -> int:
        """Get total reconnection count."""
        return self._reconnection_count

    @property
    def consecutive_failures(self) -> int:
        """Get consecutive failure count."""
        return self._consecutive_failures

    @property
    def is_stable(self) -> bool:
        """Determine if connection is considered stable."""
        # Connection is stable if:
        # - No consecutive failures
        # - Uptime > 95%
        # - Average latency is reasonable (< 1000ms) or no samples yet
        return (
            self._consecutive_failures == 0
            and self.uptime_percentage > 95.0
            and (self.average_latency < 1000.0 or not self._latency_samples)
        )


class NodeHealthMonitor:
    """
    Monitors node health and provides a health score for intelligent
    node selection and failover decisions.
    """

    __slots__ = (
        "_circuit_breaker_threshold",
        "_circuit_open",
        "_circuit_open_time",
        "_circuit_timeout",
        "_quality_tracker",
    )

    def __init__(
        self,
        circuit_breaker_threshold: int = 5,
        circuit_timeout: float = 60.0,
    ) -> None:
        self._quality_tracker = ConnectionQualityTracker()
        self._circuit_breaker_threshold: int = circuit_breaker_threshold
        self._circuit_open: bool = False
        self._circuit_open_time: float = 0.0
        self._circuit_timeout: float = circuit_timeout

    @property
    def quality_tracker(self) -> ConnectionQualityTracker:
        """Get the connection quality tracker."""
        return self._quality_tracker

    @property
    def is_circuit_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self._circuit_open:
            # Check if timeout has passed
            if time.time() - self._circuit_open_time >= self._circuit_timeout:
                self._circuit_open = False
                self._quality_tracker._consecutive_failures = 0
                return False
        return self._circuit_open

    def check_circuit_breaker(self) -> None:
        """Open the circuit breaker if consecutive failures reached the threshold.

        This can only open the circuit, never close it — closing happens via
        `record_success()`, or lazily the next time `is_circuit_open` is read
        after `circuit_timeout` has elapsed.
        """
        if self._quality_tracker.consecutive_failures >= self._circuit_breaker_threshold:
            if not self._circuit_open:
                self._circuit_open = True
                self._circuit_open_time = time.time()

    def record_success(self) -> None:
        """Record a successful operation."""
        self._quality_tracker.record_connection_success()
        if self._circuit_open:
            self._circuit_open = False

    def record_failure(self) -> None:
        """Record a failed operation."""
        self._quality_tracker.record_connection_failure()
        self.check_circuit_breaker()

    def record_reconnection(self) -> None:
        """Record a reconnection event."""
        self._quality_tracker.record_reconnection()

    def get_health_score(self, current_latency: float, player_count: int) -> float:
        """
        Calculate a health score from 0.0 (worst) to 100.0 (best).

        Factors:
        - Latency (40% weight)
        - Uptime (30% weight)
        - Player load (20% weight)
        - Connection stability (10% weight)
        """
        if self.is_circuit_open:
            return 0.0

        # Latency score (0-100, lower latency is better)
        if current_latency < 0:
            latency_score = 0.0
        elif current_latency < 50:
            latency_score = 100.0
        elif current_latency < 150:
            latency_score = 80.0
        elif current_latency < 300:
            latency_score = 60.0
        elif current_latency < 500:
            latency_score = 40.0
        elif current_latency < 1000:
            latency_score = 20.0
        else:
            latency_score = 10.0

        # Uptime score (0-100)
        uptime_score = min(100.0, self._quality_tracker.uptime_percentage)

        # Player load score (0-100, fewer players is better)
        # Assume 100 players is a reasonable max load
        player_load_score = max(0.0, 100.0 - (player_count * 1.0))

        # Stability score (0-100)
        stability_score = 100.0 if self._quality_tracker.is_stable else 50.0
        if self._quality_tracker.reconnection_count > 10:
            stability_score *= 0.5

        # Weighted average
        health_score = (
            latency_score * 0.4
            + uptime_score * 0.3
            + player_load_score * 0.2
            + stability_score * 0.1
        )

        return health_score


def voice_field(data: Any, key: str) -> Any:
    if isinstance(data, dict):
        return data.get(key)
    return getattr(data, key, None)
