"""Inspect and signal a process only while its PID and creation time still match."""

import os
from dataclasses import dataclass
from typing import Literal

import psutil

from .models import ProcessDetails, ProcessIdentity


class IdentityChanged(Exception):
    """The selected PID now belongs to another process."""


def verified_process(identity: ProcessIdentity) -> psutil.Process:
    proc = psutil.Process(identity.pid)
    if proc.create_time() != identity.created or not proc.is_running():
        raise IdentityChanged
    return proc


def control_unavailable(identity: ProcessIdentity | None) -> str | None:
    if identity is None:
        return "Process identity is unavailable; refresh and select the process again."
    if identity.pid <= 1 or identity.pid == os.getpid():
        return "This process is protected from termination in netshow."
    return None


class ProcessInspector:
    """Retain the CPU baseline between samples, never across process identities."""

    def __init__(self, identity: ProcessIdentity | None) -> None:
        self.identity = identity
        self.proc: psutil.Process | None = None
        self.static_fields: list[tuple[str, str]] | None = None

    def sample(self) -> ProcessDetails:
        if self.identity is None:
            return ProcessDetails(None, (), "Process identity is unavailable.")
        try:
            verified_process(self.identity)
            first = self.proc is None
            if self.proc is None:
                self.proc = verified_process(self.identity)
            proc = self.proc
            if self.static_fields is None:
                fields = []
                for label, getter in (
                    ("Name", proc.name),
                    ("Owner", proc.username),
                    ("Executable", proc.exe),
                    ("Working directory", proc.cwd),
                ):
                    try:
                        fields.append((label, getter() or "Unavailable"))
                    except (psutil.AccessDenied, OSError):
                        fields.append((label, "Permission denied"))
                try:
                    fields.append(("Command", " ".join(proc.cmdline()) or "Unavailable"))
                except (psutil.AccessDenied, OSError):
                    fields.append(("Command", "Permission denied"))
                self.static_fields = fields
            fields = list(self.static_fields)
            with proc.oneshot():
                for label, getter in (
                    ("Status", proc.status),
                    ("Threads", lambda: str(proc.num_threads())),
                    ("Memory", lambda: f"{proc.memory_percent():.2f}%"),
                    ("CPU", lambda: f"{proc.cpu_percent():.1f}%"),
                ):
                    try:
                        value = getter()
                        fields.append((label, "Sampling…" if first and label == "CPU" else value))
                    except (psutil.AccessDenied, OSError):
                        fields.append((label, "Permission denied"))
            return ProcessDetails(self.identity, tuple(fields))
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            return ProcessDetails(self.identity, (), "Process exited.")
        except IdentityChanged:
            return ProcessDetails(self.identity, (), "PID was reused; select the process again.")
        except (psutil.AccessDenied, OSError):
            return ProcessDetails(self.identity, (), "Permission denied inspecting this process.")


@dataclass(frozen=True)
class ProcessOutcome:
    state: Literal["exited", "alive", "denied", "changed", "protected", "error"]
    message: str


def signal_process(identity: ProcessIdentity, *, force: bool = False) -> ProcessOutcome:
    reason = control_unavailable(identity)
    if reason:
        return ProcessOutcome("protected", reason)
    try:
        proc = verified_process(identity)
        # psutil also checks PID reuse when sending the signal.
        if force:
            proc.kill()
        else:
            proc.terminate()
        proc.wait(timeout=3)
        return ProcessOutcome("exited", f"Process {identity.pid} exited.")
    except psutil.TimeoutExpired:
        return ProcessOutcome("alive", f"Process {identity.pid} is still running after 3 seconds.")
    except psutil.NoSuchProcess:
        return ProcessOutcome("exited", f"Process {identity.pid} has already exited.")
    except IdentityChanged:
        return ProcessOutcome("changed", "PID was reused. No signal was sent.")
    except (psutil.AccessDenied, PermissionError):
        return ProcessOutcome("denied", "Permission denied. No elevated privileges were requested.")
    except OSError as error:
        return ProcessOutcome("error", f"Unable to signal process: {error}")
