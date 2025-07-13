import os
import time
from typing import Any, Optional, TypedDict, Union, cast

import psutil
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import (
    Container,
    Horizontal,
    ScrollableContainer,
    Vertical,
)
from textual.reactive import reactive
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Static,
)

from .helpers import get_lsof_conns, get_psutil_conns
from .styles import CSS

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


class ConnectionDetailScreen(Screen):
    """Screen for displaying detailed information about a selected connection."""

    BINDINGS = [("escape", "app.pop_screen", "Back to connections")]

    def __init__(self, connection_data: ConnectionData):
        super().__init__()
        self.connection_data = connection_data
        self.process_info = self._get_process_info(connection_data["pid"])

    def _get_status_icon(self, status: str) -> str:
        """Get an appropriate icon for connection status."""
        # Check if parent app has emoji toggle disabled
        if hasattr(self.app, "show_emojis") and not self.app.show_emojis:
            return ""
        status_icons = {
            "ESTABLISHED": "✅",
            "LISTEN": "👂",
            "TIME_WAIT": "⏳",
            "CLOSE_WAIT": "⏸️",
            "SYN_SENT": "📤",
            "SYN_RECV": "📥",
            "FIN_WAIT1": "🔄",
            "FIN_WAIT2": "🔁",
            "CLOSING": "🔚",
            "LAST_ACK": "🏁",
        }
        return status_icons.get(status, "❓")

    def _get_process_info(self, pid_str: str) -> dict:
        """Get additional process information if PID is available."""
        if pid_str == "-":
            return {}

        try:
            pid = int(pid_str)
            proc = psutil.Process(pid)
            return {
                "name": proc.name(),
                "exe": proc.exe(),
                "cmd": " ".join(proc.cmdline()),
                "create_time": proc.create_time(),
                "status": proc.status(),
                "username": proc.username(),
                "cwd": proc.cwd(),
                "num_threads": proc.num_threads(),
                "cpu_percent": proc.cpu_percent(interval=0.1),
                "memory_percent": proc.memory_percent(),
                "open_files": proc.open_files(),
                "connections": proc.connections(),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
            return {}

    def compose(self) -> ComposeResult:
        """Compose the detail screen layout."""
        yield Header(show_clock=True)

        with ScrollableContainer():
            # Check emoji setting from parent app
            show_emojis = getattr(self.app, "show_emojis", True)
            title_prefix = "🔗 " if show_emojis else ""
            yield Static(
                f"{title_prefix}Connection Details: {self.connection_data['friendly']}",
                id="detail_title",
            )

            with Horizontal(id="main_content"):
                with Container(id="connection_details"):
                    conn_prefix = "🌐 " if show_emojis else ""
                    pid_prefix = "🆔 " if show_emojis else ""
                    proc_prefix = "⚙️ " if show_emojis else ""
                    friendly_prefix = "🏷️  " if show_emojis else ""
                    local_prefix = "🏠 " if show_emojis else ""
                    remote_prefix = "🌐 " if show_emojis else ""

                    yield Static(
                        f"{conn_prefix}Connection Info", classes="detail_title"
                    )
                    yield Static(
                        f"{pid_prefix}PID: {self.connection_data['pid']}",
                        classes="detail_item",
                    )
                    yield Static(
                        f"{proc_prefix}Process: {self.connection_data['proc']}",
                        classes="detail_item",
                    )
                    yield Static(
                        f"{friendly_prefix}Friendly Name: {self.connection_data['friendly']}",
                        classes="detail_item",
                    )
                    yield Static(
                        f"{local_prefix}Local Address: {self.connection_data['laddr']}",
                        classes="detail_item",
                        markup=False,
                    )
                    yield Static(
                        f"{remote_prefix}Remote Address: {self.connection_data['raddr']}",
                        classes="detail_item",
                        markup=False,
                    )

                    status = self.connection_data["status"]
                    status_icon = self._get_status_icon(status)
                    yield Static(
                        f"{status_icon} Status: {status}",
                        classes=f"detail_item status-{status}",
                    )

                # Show additional process info if available
                if self.process_info:
                    with Container(id="process_info"):
                        process_title_prefix = "🔧 " if show_emojis else ""
                        exe_prefix = "📁 " if show_emojis else ""
                        cmd_prefix = "💻 " if show_emojis else ""
                        status_prefix = "📊 " if show_emojis else ""
                        user_prefix = "👤 " if show_emojis else ""
                        cwd_prefix = "📂 " if show_emojis else ""
                        threads_prefix = "🧵 " if show_emojis else ""

                        yield Static(
                            f"{process_title_prefix}Process Details",
                            classes="detail_title",
                        )
                        yield Static(
                            f"{exe_prefix}Executable: {self.process_info.get('exe', 'N/A')}",
                            classes="detail_item",
                        )
                        yield Static(
                            f"{cmd_prefix}Command Line: {self.process_info.get('cmd', 'N/A')}",
                            classes="detail_item",
                        )
                        yield Static(
                            f"{status_prefix}Status: {self.process_info.get('status', 'N/A')}",
                            classes="detail_item",
                        )
                        yield Static(
                            f"{user_prefix}User: {self.process_info.get('username', 'N/A')}",
                            classes="detail_item",
                        )
                        yield Static(
                            f"{cwd_prefix}Working Directory: {self.process_info.get('cwd', 'N/A')}",
                            classes="detail_item",
                        )
                        yield Static(
                            f"{threads_prefix}Threads: "
                            f"{self.process_info.get('num_threads', 'N/A')}",
                            classes="detail_item",
                        )

                        cpu_percent = self.process_info.get("cpu_percent", 0.0)
                        if show_emojis:
                            cpu_icon = (
                                "🔥"
                                if cpu_percent > 50
                                else "⚡" if cpu_percent > 10 else "💤"
                            )
                        else:
                            cpu_icon = ""
                        cpu_prefix = f"{cpu_icon} " if cpu_icon else ""
                        yield Static(
                            f"{cpu_prefix}CPU Usage: {cpu_percent:.1f}%",
                            classes="detail_item",
                        )

                        memory_percent = self.process_info.get("memory_percent", 0.0)
                        memory_display = (
                            f"{memory_percent:.2f}%"
                            if isinstance(memory_percent, (int, float))
                            else "N/A"
                        )
                        if show_emojis:
                            memory_icon = (
                                "🚨"
                                if memory_percent > 80
                                else "⚠️" if memory_percent > 50 else "💾"
                            )
                        else:
                            memory_icon = ""
                        memory_prefix = f"{memory_icon} " if memory_icon else ""
                        yield Static(
                            f"{memory_prefix}Memory Usage: {memory_display}",
                            classes="detail_item",
                        )

                        # Network connections from this process
                        connections = self.process_info.get("connections", [])
                        if connections:
                            conn_count = (
                                len(connections) if isinstance(connections, list) else 0
                            )
                            active_conn_prefix = "🌐 " if show_emojis else ""
                            yield Static(
                                f"{active_conn_prefix}Active Connections: {conn_count}",
                                classes="detail_item",
                            )

            with Container(id="button_container"):
                back_prefix = "🔙 " if show_emojis else ""
                yield Button(f"{back_prefix}Back to Connections", id="back_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "back_button":
            self.app.pop_screen()


class NetshowApp(App):
    """Network connection monitoring application using Textual TUI."""

    CSS = CSS
    BINDINGS = cast(
        list[Union[Binding, tuple[str, str], tuple[str, str, str]]], BASIC_KEYBINDINGS
    )

    total_connections = reactive(0)
    active_connections = reactive(0)
    listening_connections = reactive(0)
    show_filter = reactive(False)
    current_filter = reactive("")
    sort_mode = reactive("default")
    selected_interface = reactive("all")
    show_emojis = reactive(True)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.last_network_stats: Optional[Any] = None
        self.last_stats_time: Optional[float] = None
        self.filtered_connections: list[dict[str, str]] = []
        self.sound_enabled: bool = True
        self.title = "Netshow"  # Will be updated with data source
        self.debounce_timer: Optional[Timer] = None
        self.available_interfaces = self._get_available_interfaces()

    def _get_available_interfaces(self) -> list:
        """Get list of available network interfaces."""
        try:
            interfaces = ["all"] + list(psutil.net_io_counters(pernic=True).keys())
            return interfaces
        except Exception:
            return ["all"]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Vertical():
            with Container(id="stats_container"):
                with Horizontal(id="metrics_row"):
                    yield Static(
                        "📊 Connections: 0", id="conn_metric", classes="metric"
                    )
                    yield Static("⚡ Active: 0", id="active_metric", classes="metric")
                    yield Static(
                        "👂 Listening: 0", id="listen_metric", classes="metric"
                    )
                    yield Static(
                        "🔥 Bandwidth: 0 B/s (all)",
                        id="bandwidth_metric",
                        classes="metric",
                    )

            with Container(id="filter_container"):
                yield Input(
                    placeholder="🔍 Filter connections (regex supported)...",
                    id="filter_input",
                )

            yield DataTable(id="connections_table")

        yield Footer()

    def on_mount(self) -> None:
        self._update_table_columns()
        self._update_filter_placeholder()
        table = self.query_one("#connections_table", DataTable)

        # Enable cursor to allow row selection
        table.cursor_type = "row"
        table.can_focus = True

        # Hide filter initially
        filter_container = self.query_one("#filter_container")
        filter_container.display = False

        # Refresh at regular intervals
        self.timer: Timer = self.set_interval(
            REFRESH_INTERVAL, self.refresh_connections
        )
        self.refresh_connections()

        # Focus the table for keyboard navigation
        table.focus()

    def refresh_connections(self, sort_only: bool = False) -> None:
        """Refresh connection data and update the display."""
        if not sort_only:
            # Fetch fresh data from system
            self._fetch_connection_data()

        # Always update the table display
        self._update_table_display()

    def _fetch_connection_data(self) -> None:
        """Fetch connection data from the system."""
        using_root = os.geteuid() == 0

        try:
            conns = get_psutil_conns() if using_root else get_lsof_conns()
        except (psutil.AccessDenied, PermissionError):
            conns = get_lsof_conns()
            using_root = False

        # Apply filtering if active
        if self.current_filter:
            import re

            try:
                pattern = re.compile(self.current_filter, re.IGNORECASE)
                conns = [
                    c
                    for c in conns
                    if any(
                        pattern.search(str(c.get(field, "")))
                        for field in ["friendly", "proc", "laddr", "raddr", "status"]
                    )
                ]
            except re.error:
                # Invalid regex, filter by simple string matching
                filter_lower = self.current_filter.lower()
                conns = [
                    c
                    for c in conns
                    if any(
                        filter_lower in str(c.get(field, "")).lower()
                        for field in ["friendly", "proc", "laddr", "raddr", "status"]
                    )
                ]

        # Apply sorting
        if self.sort_mode == "status":
            conns.sort(key=lambda x: x["status"])
        elif self.sort_mode == "process":
            conns.sort(key=lambda x: x["friendly"].lower())

        self.filtered_connections = conns

        # Update app title with data source
        source_name = "psutil" if using_root else "lsof"
        self.title = f"Netshow ({source_name})"

    def _update_table_display(self) -> None:
        """Update the table display with current connection data."""
        table = self.query_one("#connections_table", DataTable)
        conns = self.filtered_connections

        # Capture current scroll offset & cursor row for restoration
        row_offset, col_offset = getattr(table, "scroll_offset", (0, 0))
        cursor_row = getattr(table, "cursor_row", 0)

        # Check if we can optimize by replacing rows instead of clearing
        can_optimize = (
            table.row_count == len(conns) and table.row_count > 0 and len(conns) > 100
        )  # Only optimize for large datasets

        if can_optimize:
            # Try to replace existing rows to avoid flicker
            try:
                for i, c in enumerate(conns):
                    if i >= table.row_count:
                        break

                    status_icon = self._get_status_icon(c["status"])
                    speed_indicator = self._get_speed_indicator(c)
                    status_text = (
                        f"{status_icon} {c['status']}" if status_icon else c["status"]
                    )
                    new_row = [
                        c["pid"],
                        c["friendly"],
                        c["proc"],
                        c["laddr"],
                        c["raddr"],
                        status_text,
                        speed_indicator,
                    ]

                    # Get the row key for the i-th row
                    row_keys = list(table.rows.keys())
                    if i < len(row_keys):
                        row_key = row_keys[i]
                        # Verify the row key is valid before updating
                        if row_key in table.rows:
                            columns = list(table.columns.keys())
                            if len(columns) >= 7:
                                table.update_cell(row_key, columns[0], new_row[0])
                                table.update_cell(row_key, columns[1], new_row[1])
                                table.update_cell(row_key, columns[2], new_row[2])
                                table.update_cell(row_key, columns[3], new_row[3])
                                table.update_cell(row_key, columns[4], new_row[4])
                                table.update_cell(row_key, columns[5], new_row[5])
                                table.update_cell(row_key, columns[6], new_row[6])
                        else:
                            # Row key invalid, fall back to full rebuild
                            raise ValueError("Invalid row key, falling back to rebuild")
            except Exception:
                # If optimization fails, fall back to full rebuild
                can_optimize = False

        if not can_optimize:
            # Fall back to clear and rebuild for smaller datasets or size changes
            table.clear()
            for c in conns:
                status_icon = self._get_status_icon(c["status"])
                speed_indicator = self._get_speed_indicator(c)
                status_text = (
                    f"{status_icon} {c['status']}" if status_icon else c["status"]
                )
                table.add_row(
                    c["pid"],
                    c["friendly"],
                    c["proc"],
                    c["laddr"],
                    c["raddr"],
                    status_text,
                    speed_indicator,
                )

        # Count connection types for stats
        established = listening = time_wait = 0
        for c in conns:
            status = c["status"]
            if status == "ESTABLISHED":
                established += 1
            elif status == "LISTEN":
                listening += 1
            elif status == "TIME_WAIT":
                time_wait += 1

        # Update reactive stats
        self.total_connections = len(conns)
        self.active_connections = established
        self.listening_connections = listening

        # Update metrics display
        self._update_metrics_display(len(conns), established, listening)

        # Restore scroll & cursor position
        if hasattr(table, "scroll_to"):
            table.scroll_to(row_offset, col_offset)
        if cursor_row < table.row_count and hasattr(table, "cursor_coordinate"):
            table.cursor_coordinate = (cursor_row, 0)  # type: ignore

    def _get_status_icon(self, status: str) -> str:
        """Get an appropriate icon for connection status."""
        if not self.show_emojis:
            return ""
        status_icons = {
            "ESTABLISHED": "🚀",  # More exciting!
            "LISTEN": "👂",
            "TIME_WAIT": "⏳",
            "CLOSE_WAIT": "⏸️",
            "SYN_SENT": "📤",
            "SYN_RECV": "📥",
            "FIN_WAIT1": "🔄",
            "FIN_WAIT2": "🔁",
            "CLOSING": "🔚",
            "LAST_ACK": "🏁",
        }
        return status_icons.get(status, "❓")

    def _get_speed_indicator(
        self, connection: Union[dict[str, str], ConnectionData]
    ) -> str:
        """Generate a speed indicator based on connection characteristics."""
        if not self.show_emojis:
            status = connection.get("status", "")
            if status == "LISTEN":
                return "WAIT"
            elif "WAIT" in status:
                return "WAIT"
            else:
                return "ACTIVE"
        # Placeholder until real throughput data is available
        status = connection.get("status", "")
        if status == "LISTEN":
            return "💤"  # Waiting
        elif "WAIT" in status:
            return "⏳"  # Waiting states
        else:
            return "📊"  # Default

    def _update_metrics_display(self, total: int, active: int, listening: int) -> None:
        """Update the metrics display with current stats."""
        try:
            conn_metric = self.query_one("#conn_metric", Static)
            active_metric = self.query_one("#active_metric", Static)
            listen_metric = self.query_one("#listen_metric", Static)
            bandwidth_metric = self.query_one("#bandwidth_metric", Static)

            # Emoji prefixes based on toggle state
            conn_prefix = "📊 " if self.show_emojis else ""
            active_prefix = "⚡ " if self.show_emojis else ""
            listen_prefix = "👂 " if self.show_emojis else ""
            bandwidth_prefix = "🔥 " if self.show_emojis else ""

            # Get network I/O stats for bandwidth
            try:
                if self.selected_interface == "all":
                    net_io = psutil.net_io_counters()
                    interface_label = "all"
                else:
                    net_io_per_nic = psutil.net_io_counters(pernic=True)
                    net_io_temp = net_io_per_nic.get(self.selected_interface)
                    interface_label = self.selected_interface
                    if not net_io_temp:
                        # Interface not found, fallback to all
                        interface_label = "all"
                        self.selected_interface = "all"
                    else:
                        net_io = net_io_temp

                current_time = time.time()
                if (
                    self.last_network_stats is not None
                    and self.last_stats_time is not None
                ):
                    time_diff = max(
                        0.1, current_time - self.last_stats_time
                    )  # Avoid division by zero
                    bytes_sent_diff = max(
                        0, net_io.bytes_sent - self.last_network_stats.bytes_sent
                    )
                    bytes_recv_diff = max(
                        0, net_io.bytes_recv - self.last_network_stats.bytes_recv
                    )
                    total_bandwidth = (bytes_sent_diff + bytes_recv_diff) / time_diff
                    bandwidth_text = f"{self._format_bytes(int(total_bandwidth))}/s ({interface_label})"
                else:
                    bandwidth_text = f"0 B/s ({interface_label})"
                self.last_network_stats = net_io
                self.last_stats_time = current_time
            except (AttributeError, OSError):
                bandwidth_text = "N/A"

            conn_metric.update(f"{conn_prefix}Connections: {total}")
            active_metric.update(f"{active_prefix}Active: {active}")
            listen_metric.update(f"{listen_prefix}Listening: {listening}")
            bandwidth_metric.update(f"{bandwidth_prefix}Bandwidth: {bandwidth_text}")
        except Exception:
            pass  # Gracefully handle missing widgets

    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes into human readable format."""
        if bytes_val == 0:
            return "0 B"

        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_val < 1024.0:
                if unit == "B" or bytes_val < 10:
                    return f"{int(bytes_val)} {unit}"
                else:
                    return f"{bytes_val:.1f} {unit}"
            bytes_val = int(bytes_val / 1024.0)
        return f"{bytes_val:.1f} TB"

    def _get_selected_connection_data(self, row_data: tuple) -> ConnectionData:
        """Convert row data tuple to ConnectionData dict."""
        # Extract status without icon (remove first 2 characters: icon + space)
        status_with_icon = row_data[5]
        clean_status = (
            status_with_icon[2:] if len(status_with_icon) > 2 else status_with_icon
        )

        return ConnectionData(
            pid=row_data[0],
            friendly=row_data[1],
            proc=row_data[2],
            laddr=row_data[3],
            raddr=row_data[4],
            status=clean_status,
        )

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row highlighting in the DataTable."""
        # This event fires when cursor moves over rows
        pass

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the DataTable."""
        # Pause refreshing while viewing details
        self.timer.pause()

        # Get the selected row's data
        table = self.query_one("#connections_table", DataTable)
        row_data = table.get_row(event.row_key)
        selected_data = self._get_selected_connection_data(tuple(row_data))

        # Push the detail screen
        await self.push_screen(ConnectionDetailScreen(selected_data))

    async def on_screen_resume(self) -> None:
        """Called when this screen is resumed (after popping another screen)."""
        # Resume refreshing when returning from detail view
        self.timer.resume()
        self.refresh_connections()

        # Re-focus the table for keyboard navigation
        table = self.query_one("#connections_table", DataTable)
        table.focus()

    async def action_toggle_filter(self) -> None:
        """Toggle the filter input visibility."""
        filter_container = self.query_one("#filter_container")
        filter_input = self.query_one("#filter_input", Input)

        if filter_container.display:
            filter_container.display = False
            self.show_filter = False
            # Return focus to the DataTable when filter is closed
            table = self.query_one("#connections_table", DataTable)
            table.focus()
        else:
            filter_container.display = True
            self.show_filter = True
            filter_input.focus()

    async def action_search(self) -> None:
        """Focus the search input for quick access."""
        if not self.show_filter:
            await self.action_toggle_filter()
        else:
            filter_input = self.query_one("#filter_input", Input)
            filter_input.focus()

    def action_sort_by_status(self) -> None:
        """Sort connections by status."""
        self.sort_mode = "status" if self.sort_mode != "status" else "default"
        # Re-sort existing data and update display (no need to fetch fresh data)
        if self.filtered_connections:
            if self.sort_mode == "status":
                self.filtered_connections.sort(key=lambda x: x["status"])
            else:
                # Default sort - could add timestamp-based sorting here
                pass
            self._update_table_display()
        else:
            self.refresh_connections()

    def action_sort_by_process(self) -> None:
        """Sort connections by process name."""
        self.sort_mode = "process" if self.sort_mode != "process" else "default"
        # Re-sort existing data and update display (no need to fetch fresh data)
        if self.filtered_connections:
            if self.sort_mode == "process":
                self.filtered_connections.sort(key=lambda x: x["friendly"].lower())
            else:
                # Default sort - could add timestamp-based sorting here
                pass
            self._update_table_display()
        else:
            self.refresh_connections()

    def action_toggle_interface(self) -> None:
        """Cycle through available network interfaces."""
        current_index = 0
        try:
            current_index = self.available_interfaces.index(self.selected_interface)
        except ValueError:
            pass

        next_index = (current_index + 1) % len(self.available_interfaces)
        self.selected_interface = self.available_interfaces[next_index]

        # Reset bandwidth stats when changing interface
        self.last_network_stats = None
        self.last_stats_time = None

    def action_toggle_emojis(self) -> None:
        """Toggle emoji display on/off."""
        self.show_emojis = not self.show_emojis

        # Update table columns and refresh display
        self._update_table_columns()
        self._update_filter_placeholder()

        # Force a complete refresh to update all UI elements
        self.refresh_connections()

        # Update metrics display immediately
        self._update_metrics_display(
            self.total_connections, self.active_connections, self.listening_connections
        )

    def _update_table_columns(self) -> None:
        """Update table column headers based on emoji setting."""
        table = self.query_one("#connections_table", DataTable)

        # Clear existing columns if any
        table.clear(columns=True)

        if self.show_emojis:
            table.add_columns(
                "🆔 PID",
                "🔖 Service",
                "⚙️  Process",
                "🏠 Local Address",
                "🌐 Remote Address",
                "📊 Status",
                "⚡ Speed",
            )
        else:
            table.add_columns(
                "PID",
                "Service",
                "Process",
                "Local Address",
                "Remote Address",
                "Status",
                "Speed",
            )

    def _get_filter_placeholder(self) -> str:
        """Get filter input placeholder text based on emoji setting."""
        if self.show_emojis:
            return "🔍 Filter connections (regex supported)..."
        else:
            return "Filter connections (regex supported)..."

    def _update_filter_placeholder(self) -> None:
        """Update filter input placeholder."""
        try:
            filter_input = self.query_one("#filter_input", Input)
            filter_input.placeholder = self._get_filter_placeholder()
        except Exception:
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle filter input changes."""
        if event.input.id == "filter_input":
            self.current_filter = event.value
            # Cancel existing debounce timer if it exists
            if self.debounce_timer is not None:
                self.debounce_timer.stop()
            # Create new debounce timer
            self.debounce_timer = self.set_timer(0.5, self.refresh_connections)


if __name__ == "__main__":
    NetshowApp().run()
