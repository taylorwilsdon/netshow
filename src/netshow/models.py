"""Data shared by collectors and the UI; no rendered values live here."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    created: float


@dataclass(frozen=True)
class Connection:
    pid: int | None
    process: str
    friendly: str
    local: str
    remote: str
    status: str
    identity: ProcessIdentity | None = None
    fd: int = -1

    @property
    def key(self) -> str:
        # Status can change without the socket or process changing.
        return repr((self.pid, self.identity, self.fd, self.local, self.remote))


@dataclass(frozen=True)
class CollectionResult:
    connections: tuple[Connection, ...] = ()
    source: str = "psutil"
    limited: bool = False
    error: str | None = None


@dataclass(frozen=True)
class BandwidthSample:
    interface: str = "all"
    received: float = 0
    sent: float = 0
    available: bool = True


@dataclass(frozen=True)
class ProcessDetails:
    identity: ProcessIdentity | None
    fields: tuple[tuple[str, str], ...]
    error: str | None = None
