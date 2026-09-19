"""Pure filtering and formatting, independent of system collection."""

import re
import unicodedata
from collections.abc import Iterable

from .models import Connection

STATUS_ICONS = {"ESTABLISHED": "●", "LISTEN": "◉", "TIME_WAIT": "◷", "CLOSE_WAIT": "◷"}


def literal(value: str) -> str:
    """Keep user data literal and prevent terminal control sequences from leaking."""
    return "".join(c if not unicodedata.category(c).startswith("C") else " " for c in value)


def format_bytes(value: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TiB"


def address(value: str, expanded: bool) -> str:
    if not expanded and value.startswith("[") and "]:" in value:
        return "[…]:" + value.rsplit("]:", 1)[1]
    return value


def select_connections(
    connections: Iterable[Connection], query: str, sort: str
) -> tuple[list[Connection], bool]:
    invalid = False
    try:
        pattern = re.compile(query, re.IGNORECASE)
    except re.error:
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        invalid = True
    selected = [
        c
        for c in connections
        if any(
            pattern.search(field)
            for field in (str(c.pid or ""), c.process, c.friendly, c.local, c.remote, c.status)
        )
    ]
    # A deterministic default also breaks ties for the other sorts.
    selected.sort(key=lambda c: (c.pid or -1, c.local, c.remote, c.fd))
    if sort == "status":
        selected.sort(key=lambda c: c.status)
    elif sort == "process":
        selected.sort(key=lambda c: c.friendly.casefold())
    return selected, invalid
