"""Friendly service names with bounded, short-lived Docker discovery."""

import re
import subprocess
import time

STATIC_MAP = {
    "rapportd": "Handoff Sync Process",
    "IPNExtension": "Tailscale",
    "Code H": "VS Code",
    "Adobe H": "Adobe",
}
_docker_names: dict[str, str] = {}
_docker_expires = 0.0


def _docker_container_lookup() -> dict[str, str]:
    global _docker_names, _docker_expires
    now = time.monotonic()
    if now >= _docker_expires:
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.ID}} {{.Names}}"],
                capture_output=True,
                text=True,
                timeout=2,
                check=True,
            )
            _docker_names = dict(
                parts
                for line in result.stdout.splitlines()
                if len(parts := line.split(maxsplit=1)) == 2
            )
        except (OSError, subprocess.SubprocessError):
            _docker_names = {}
        _docker_expires = now + 30
    return _docker_names


def get_friendly_name(proc_name: str, pid: int, cmdline: str | None) -> str:
    """Keep the original helper interface for existing callers."""
    if proc_name in STATIC_MAP:
        return STATIC_MAP[proc_name]
    if re.match("plex", proc_name, re.I):
        return "Plex Media Server"
    if re.match(r"com\.docker", proc_name, re.I):
        count = len(_docker_container_lookup())
        return f"Docker Desktop ({count} containers)" if count else "Docker Desktop"
    if cmdline and re.search(r"\b[0-9a-f]{12,64}\b", cmdline):
        for container_id, name in _docker_container_lookup().items():
            if container_id in cmdline:
                return f"Docker: {name}"
    return proc_name
