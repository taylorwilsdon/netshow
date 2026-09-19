"""TCP collection with explicit source, visibility, and failure information."""

import os
import re
import subprocess

import psutil

from .helpers import get_friendly_name
from .models import CollectionResult, Connection, ProcessIdentity


def process_metadata(
    pid: int | None, fallback: str = "-"
) -> tuple[str, str, ProcessIdentity | None]:
    if pid is None:
        return fallback, fallback, None
    name, command, identity = fallback, "", None
    try:
        proc = psutil.Process(pid)
        identity = ProcessIdentity(pid, proc.create_time())
        with proc.oneshot():
            try:
                name = proc.name()
            except psutil.AccessDenied:
                pass
            try:
                command = " ".join(proc.cmdline())
            except psutil.AccessDenied:
                pass
        if not proc.is_running():
            identity = None
    except (psutil.Error, OSError):
        identity = None
    return name, get_friendly_name(name, pid, command), identity


def endpoint(value: tuple[str, int] | tuple[()]) -> str:
    if not value:
        return ""
    host, port = value
    return f"[{host}]:{port}" if ":" in host else f"{host}:{port}"


def collect_psutil() -> tuple[Connection, ...]:
    metadata: dict[int | None, tuple[str, str, ProcessIdentity | None]] = {}
    connections = []
    for socket in psutil.net_connections(kind="tcp"):
        pid = socket.pid
        if pid not in metadata:
            metadata[pid] = process_metadata(pid)
        name, friendly, identity = metadata[pid]
        connections.append(
            Connection(
                pid,
                name,
                friendly,
                endpoint(socket.laddr),
                endpoint(socket.raddr),
                socket.status,
                identity,
                socket.fd,
            )
        )
    return tuple(connections)


def parse_lsof(output: str) -> tuple[Connection, ...]:
    """Parse NUL-delimited -F output. Newlines delimit process/file records."""
    pid: int | None = None
    name = "-"
    fields: dict[str, str] = {}
    connections = []

    def flush() -> None:
        if pid is None or not fields.get("n"):
            return
        local, _, remote = fields["n"].partition("->")
        descriptor = re.match(r"\d+", fields.get("f", ""))
        connections.append(
            Connection(
                pid,
                name,
                name,
                local,
                remote,
                fields.get("state", "UNKNOWN"),
                fd=int(descriptor[0]) if descriptor else -1,
            )
        )

    for raw in output.split("\0"):
        field = raw.lstrip("\n")
        if not field:
            continue
        tag, value = field[0], field[1:]
        if tag in ("p", "f"):
            flush()
            fields = {}
        if tag == "p":
            pid = int(value) if value.isdigit() else None
            name = "-"
        elif tag == "c":
            name = value
        elif tag == "T" and value.startswith("ST="):
            fields["state"] = value[3:]
        else:
            fields[tag] = value
    flush()
    return tuple(connections)


def collect_lsof() -> CollectionResult:
    try:
        result = subprocess.run(
            ["lsof", "-nP", "-iTCP", "-F0pcfnT"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except FileNotFoundError:
        return CollectionResult(source="lsof", error="lsof is not installed")
    except subprocess.TimeoutExpired:
        return CollectionResult(source="lsof", error="lsof timed out after 5 seconds")
    except OSError as error:
        return CollectionResult(source="lsof", error=f"lsof unavailable: {error}")
    # lsof uses 1 for no matches; stderr distinguishes failures from an empty result.
    if result.returncode not in (0, 1) or (result.stderr.strip() and not result.stdout):
        return CollectionResult(source="lsof", error=result.stderr.strip() or "lsof failed")
    parsed = parse_lsof(result.stdout)
    if result.stdout.strip() and not parsed:
        return CollectionResult(source="lsof", error="Unable to parse lsof TCP records")
    metadata: dict[int | None, tuple[str, str, ProcessIdentity | None]] = {}
    connections = []
    for connection in parsed:
        if connection.pid not in metadata:
            metadata[connection.pid] = process_metadata(connection.pid, connection.process)
        name, friendly, identity = metadata[connection.pid]
        connections.append(
            Connection(
                connection.pid,
                name,
                friendly,
                connection.local,
                connection.remote,
                connection.status,
                identity,
                connection.fd,
            )
        )
    return CollectionResult(
        tuple(connections), "lsof", limited=os.geteuid() != 0 or bool(result.stderr)
    )


def collect_connections() -> CollectionResult:
    try:
        return CollectionResult(collect_psutil(), limited=os.geteuid() != 0)
    except (psutil.AccessDenied, PermissionError):
        result = collect_lsof()
        if result.error:
            return CollectionResult(source="lsof", error=f"psutil access denied; {result.error}")
        return result
    except (OSError, psutil.Error) as error:
        return CollectionResult(error=f"Connection collection failed: {error}")
