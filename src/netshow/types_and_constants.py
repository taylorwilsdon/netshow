from typing import TypedDict

# Constants
REFRESH_INTERVAL = 3.0  # seconds
CONNECTION_COLUMNS = ["pid", "friendly", "proc", "laddr", "raddr", "status"]
BASIC_KEYBINDINGS = [
    ("q", "quit", "Quit"),
    ("ctrl+r", "refresh", "Force Refresh"),
    ("f", "toggle_filter", "Filter"),
    ("s", "sort_by_status", "Sort by Status"),
    ("p", "sort_by_process", "Sort by Process"),
    ("i", "toggle_interface", "Interface"),
    ("e", "toggle_emojis", "Emojis"),
    ("ctrl+c", "quit", "Hard Quit"),
    ("/", "search", "Search"),
]


class ConnectionData(TypedDict):
    """Type definition for connection data."""

    pid: str
    friendly: str
    proc: str
    laddr: str
    raddr: str
    status: str


class NetworkStats(TypedDict):
    """Type definition for network statistics."""

    total_connections: int
    established: int
    listening: int
    time_wait: int
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    timestamp: float