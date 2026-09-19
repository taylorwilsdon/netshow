"""One owner for interface counters and their monotonic sampling baseline."""

import time
from collections import deque

import psutil

from .models import BandwidthSample


class BandwidthSampler:
    def __init__(self) -> None:
        self.interfaces = ["all"]
        self.history: deque[float] = deque(maxlen=60)
        self.previous: tuple[str, float, int, int] | None = None

    def sample(self, interface: str) -> BandwidthSample:
        try:
            counters = psutil.net_io_counters(pernic=True)
        except (OSError, psutil.Error):
            self.previous = None
            self.history.clear()
            return BandwidthSample(interface, available=False)
        self.interfaces = ["all", *sorted(counters)]
        if interface not in self.interfaces:
            interface = "all"
        if not counters:
            self.previous = None
            self.history.clear()
            return BandwidthSample(interface, available=False)
        selected = list(counters.values()) if interface == "all" else [counters[interface]]
        return self.observe(
            interface,
            time.monotonic(),
            sum(c.bytes_recv for c in selected),
            sum(c.bytes_sent for c in selected),
        )

    def observe(self, interface: str, now: float, received: int, sent: int) -> BandwidthSample:
        previous = self.previous
        self.previous = (interface, now, received, sent)
        if previous is None or previous[0] != interface:
            self.history.clear()
            return BandwidthSample(interface)
        elapsed = now - previous[1]
        if elapsed <= 0 or received < previous[2] or sent < previous[3]:
            self.history.clear()
            return BandwidthSample(interface)
        sample = BandwidthSample(
            interface, (received - previous[2]) / elapsed, (sent - previous[3]) / elapsed
        )
        self.history.append(sample.received + sample.sent)
        return sample
