"""Helper functions for gathering network connections."""

import re
import subprocess
from functools import lru_cache
from typing import Optional

import psutil

# Friendly-name helpers
STATIC_MAP = {
    "rapportd": "Handoff Sync Process",
    "IPNExtension": "Tailscale",
    "Code\x20H": "VSCode",
    "Adobe\x20H": "Adobe",
}

DOCKER_RE = re.compile(r"com\.docker", re.I)
PLEX_RE = re.compile(r"plex", re.I)


@lru_cache(maxsize=1)
def _docker_container_lookup() -> dict[str, str]:
    """Look up Docker container IDs and names."""
    try:
        out = subprocess.check_output(
            ["docker", "ps", "--format", "{{.ID}} {{.Names}}"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return {}
    return dict(line.split(maxsplit=1) for line in out.splitlines())


def get_friendly_name(proc_name: str, pid: int, cmdline: Optional[str]) -> str:
    """Get a friendly name for a process."""
    if proc_name in STATIC_MAP:
        return STATIC_MAP[proc_name]
    if PLEX_RE.match(proc_name):
        return "Plex Media Server"
    if DOCKER_RE.match(proc_name):
        cnt = len(_docker_container_lookup())
        return f"Docker Desktop ({cnt} containers)" if cnt else "Docker Desktop"
    if cmdline:
        for cid, cname in _docker_container_lookup().items():
            if cid in cmdline:
                return f"Docker: {cname}"
    return proc_name


# Connection gathering helpers
def get_psutil_conns() -> list[dict[str, str]]:
    """Get network connections using psutil."""
    conns = []
    for conn in psutil.net_connections(kind="tcp"):
        pid = conn.pid if conn.pid else None
        try:
            proc = psutil.Process(pid) if pid else None
            proc_name = proc.name() if proc else "-"
            cmdline = " ".join(proc.cmdline()) if proc else ""
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            proc_name, cmdline = "-", ""
        conns.append(
            {
                "pid": str(pid) if pid else "-",
                "proc": proc_name,
                "friendly": get_friendly_name(proc_name, pid or 0, cmdline),
                "laddr": (
                    f"[{conn.laddr.ip}]:{conn.laddr.port}"
                    if conn.laddr and ":" in conn.laddr.ip
                    else f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
                ),
                "raddr": (
                    f"[{conn.raddr.ip}]:{conn.raddr.port}"
                    if conn.raddr and ":" in conn.raddr.ip
                    else f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ""
                ),
                "status": conn.status,
            }
        )
    return conns


def get_lsof_conns() -> list[dict[str, str]]:
    """Get network connections using lsof."""
    try:
        output = subprocess.check_output(
            ["lsof", "-nP", "-iTCP", "-sTCP:ESTABLISHED,LISTEN"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return []
    except subprocess.CalledProcessError as e:
        # lsof returns exit code 1 in some environments even with valid output
        # If we have output, proceed with parsing; otherwise return empty list
        if e.output:
            output = e.output
        else:
            return []

    conns = []
    pattern = re.compile(
        r"^(?P<proc>\S+)\s+(?P<pid>\d+)\s+\S+\s+\S+\s+\S+\s+\S+\s+\S+\s+TCP\s+(?P<addr>.+)$"
    )
    for line in output.splitlines()[1:]:
        m = pattern.match(line)
        if not m:
            continue
        proc_name = m["proc"]
        pid = int(m["pid"])
        addr_field = m["addr"]
        status = ""
        if "(" in addr_field:
            addr_field, status = addr_field.rsplit("(", 1)
            status = status.rstrip(")")
        laddr, raddr = (addr_field.split("->", 1) + [""])[:2]
        laddr, raddr = laddr.strip(), raddr.strip()
        try:
            cmdline = " ".join(psutil.Process(pid).cmdline())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            cmdline = ""
        conns.append(
            {
                "pid": str(pid),
                "proc": proc_name,
                "friendly": get_friendly_name(proc_name, pid, cmdline),
                "laddr": laddr,
                "raddr": raddr,
                "status": status,
            }
        )
    return conns
