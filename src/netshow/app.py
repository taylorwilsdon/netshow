import os
import time
from collections import deque
from typing import Any, Optional, Union, cast

import psutil
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import DataTable, Footer, Header, Input, Sparkline, Static

from .detail_screen import ConnectionDetailScreen
from .helpers import get_lsof_conns, get_psutil_conns
from .styles import CSS
from .types_and_constants import (
    BASIC_KEYBINDINGS,
    REFRESH_INTERVAL,
    ConnectionData,
)


class NetshowApp(App):
    """Network connection monitoring application using Textual TUI."""

    CSS = CSS
    BINDINGS = cast(list[Union[Binding, tuple[str, str], tuple[str, str, str]]], BASIC_KEYBINDINGS)

    total_connections = reactive(0)
    active_connections = reactive(0)
    listening_connections = reactive(0)
    show_filter = reactive(False)
    current_filter = reactive("")
    sort_mode = reactive("default")
    selected_interface = reactive("all")
    show_emojis = reactive(True)
    expand_ipv6 = reactive(False)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.last_network_stats: Optional[Any] = None
        self.last_stats_time: Optional[float] = None
        self.filtered_connections: list[dict[str, str]] = []
        self.sound_enabled: bool = True
        self.title = "Netshow"  # Will be updated with data source
        self.debounce_timer: Optional[Timer] = None
        self.available_interfaces = self._get_available_interfaces()
        self.bandwidth_history: deque[float] = deque(maxlen=20)  # Last 20 samples

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
                    yield Static("📊 0", id="conn_metric", classes="metric")
                    yield Static("⚡ 0", id="active_metric", classes="metric")
                    yield Static("👂 0", id="listen_metric", classes="metric")
                    yield Static("🔥 0 B/s", id="bandwidth_metric", classes="metric bandwidth")
                yield Sparkline([], id="bandwidth_spark")

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
        self.timer: Timer = self.set_interval(REFRESH_INTERVAL, self.refresh_connections)
        self.refresh_connections()

        # Focus the table for keyboard navigation
        table.focus()

    def on_resize(self) -> None:
        """Handle terminal resize - update metrics display."""
        self._update_metrics_display(
            self.total_connections, self.active_connections, self.listening_connections
        )

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

    def _truncate_addr(self, addr: str) -> str:
        """Truncate IPv6 addresses for compact display."""
        if not addr or self.expand_ipv6:
            return addr
        # Check for IPv6 (contains multiple colons or brackets)
        if addr.startswith("[") or addr.count(":") > 1:
            # Extract port if present
            if "]:" in addr:
                ip, port = addr.rsplit(":", 1)
                return f"[…]:{port}"
            elif addr.startswith("["):
                return "[…]"
            # Bare IPv6 with port (ip:port where ip has multiple colons)
            parts = addr.rsplit(":", 1)
            if len(parts) == 2 and parts[0].count(":") >= 1:
                return f"…:{parts[1]}"
            return "…"
        return addr

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

                    status_styled = self._get_status_styled(c["status"])
                    speed_indicator = self._get_speed_indicator(c)
                    new_row = [
                        c["pid"],
                        c["friendly"],
                        c["proc"],
                        self._truncate_addr(c["laddr"]),
                        self._truncate_addr(c["raddr"]),
                        status_styled,
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
                status_styled = self._get_status_styled(c["status"])
                speed_indicator = self._get_speed_indicator(c)
                table.add_row(
                    c["pid"],
                    c["friendly"],
                    c["proc"],
                    self._truncate_addr(c["laddr"]),
                    self._truncate_addr(c["raddr"]),
                    status_styled,
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

    def _get_status_styled(self, status: str) -> Text:
        """Get a Rich Text styled status with color coding (Solarized)."""
        status_styles = {
            "ESTABLISHED": ("bold #859900", "🚀"),  # green
            "LISTEN": ("bold #268bd2", "👂"),  # blue
            "TIME_WAIT": ("#b58900", "⏳"),  # yellow
            "CLOSE_WAIT": ("bold #dc322f", "⏸️"),  # red
            "SYN_SENT": ("#d33682", "📤"),  # magenta
            "SYN_RECV": ("#d33682", "📥"),  # magenta
            "FIN_WAIT1": ("#b58900", "🔄"),  # yellow
            "FIN_WAIT2": ("#b58900", "🔁"),  # yellow
            "CLOSING": ("#dc322f", "🔚"),  # red
            "LAST_ACK": ("#dc322f", "🏁"),  # red
        }
        style, icon = status_styles.get(status, ("#586e75", "❓"))  # base01
        if self.show_emojis:
            return Text(f"{icon} {status}", style=style)
        return Text(status, style=style)

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

    def _get_speed_indicator(self, connection: Union[dict[str, str], ConnectionData]) -> str:
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
            bandwidth_spark = self.query_one("#bandwidth_spark", Sparkline)

            # Check terminal width for adaptive display
            width = self.size.width
            compact = width < 100
            show_spark = width >= 80

            # Emoji prefixes based on toggle state
            conn_icon = "📊 " if self.show_emojis else ""
            active_icon = "⚡ " if self.show_emojis else ""
            listen_icon = "👂 " if self.show_emojis else ""
            bw_icon = "🔥 " if self.show_emojis else ""

            # Get network I/O stats for bandwidth
            total_bandwidth = 0.0
            interface_label = self.selected_interface
            try:
                if self.selected_interface == "all":
                    net_io = psutil.net_io_counters()
                else:
                    net_io_per_nic = psutil.net_io_counters(pernic=True)
                    net_io_temp = net_io_per_nic.get(self.selected_interface)
                    if not net_io_temp:
                        interface_label = "all"
                        self.selected_interface = "all"
                        net_io = psutil.net_io_counters()
                    else:
                        net_io = net_io_temp

                current_time = time.time()
                if self.last_network_stats is not None and self.last_stats_time is not None:
                    time_diff = max(0.1, current_time - self.last_stats_time)
                    bytes_sent_diff = max(0, net_io.bytes_sent - self.last_network_stats.bytes_sent)
                    bytes_recv_diff = max(0, net_io.bytes_recv - self.last_network_stats.bytes_recv)
                    total_bandwidth = (bytes_sent_diff + bytes_recv_diff) / time_diff
                self.last_network_stats = net_io
                self.last_stats_time = current_time
            except (AttributeError, OSError):
                pass

            # Update sparkline
            self.bandwidth_history.append(total_bandwidth)
            bandwidth_spark.data = list(self.bandwidth_history)
            bandwidth_spark.display = show_spark

            # Adaptive labels based on width
            if compact:
                conn_metric.update(f"{conn_icon}{total}")
                active_metric.update(f"{active_icon}{active}")
                listen_metric.update(f"{listen_icon}{listening}")
                bandwidth_metric.update(f"{bw_icon}{self._format_bytes(int(total_bandwidth))}/s")
            else:
                conn_metric.update(f"{conn_icon}Conn: {total}")
                active_metric.update(f"{active_icon}Active: {active}")
                listen_metric.update(f"{listen_icon}Listen: {listening}")
                iface = f" ({interface_label})" if width >= 120 else ""
                bandwidth_metric.update(
                    f"{bw_icon}{self._format_bytes(int(total_bandwidth))}/s{iface}"
                )
        except Exception:
            pass

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
        # Extract status - handle both Rich Text objects and plain strings
        status_cell = row_data[5]
        if isinstance(status_cell, Text):
            # Rich Text object - extract plain text and remove emoji prefix
            status_text = status_cell.plain
            # Remove emoji prefix if present (emoji + space = ~3 chars)
            clean_status = status_text.split(" ", 1)[-1] if " " in status_text else status_text
        else:
            # Plain string - remove first 2 characters (icon + space)
            clean_status = status_cell[2:] if len(status_cell) > 2 else status_cell

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
        self.refresh_connections()

        # Update metrics display immediately
        self._update_metrics_display(
            self.total_connections, self.active_connections, self.listening_connections
        )

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

    def action_toggle_ipv6(self) -> None:
        """Toggle IPv6 address expansion."""
        self.expand_ipv6 = not self.expand_ipv6
        self._update_table_display()

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
