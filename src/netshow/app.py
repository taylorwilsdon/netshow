import os
from datetime import datetime
from typing import TypedDict

import psutil
from textual import events
from textual.app import App, ComposeResult
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
    Static,
)

from .helpers import get_lsof_conns, get_psutil_conns
from .styles import CSS

# Constants
REFRESH_INTERVAL = 3.0  # seconds
CONNECTION_COLUMNS = ["pid", "friendly", "proc", "laddr", "raddr", "status"]


class ConnectionData(TypedDict):
    """Type definition for connection data."""

    pid: str
    friendly: str
    proc: str
    laddr: str
    raddr: str
    status: str


class ConnectionDetailScreen(Screen):
    """Screen for displaying detailed information about a selected connection."""

    BINDINGS = [("escape", "app.pop_screen", "Back to connections")]

    def __init__(self, connection_data: ConnectionData):
        super().__init__()
        self.connection_data = connection_data
        self.process_info = self._get_process_info(connection_data["pid"])

    def _get_status_icon(self, status: str) -> str:
        """Get an appropriate icon for connection status."""
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
            yield Static(
                f"🔗 Connection Details: {self.connection_data['friendly']}",
                id="detail_title",
            )

            with Horizontal(id="main_content"):
                with Container(id="connection_details"):
                    yield Static("🌐 Connection Info", classes="detail_title")
                    yield Static(
                        f"🆔 PID: {self.connection_data['pid']}", classes="detail_item"
                    )
                    yield Static(
                        f"⚙️ Process: {self.connection_data['proc']}",
                        classes="detail_item",
                    )
                    yield Static(
                        f"🏷️  Friendly Name: {self.connection_data['friendly']}",
                        classes="detail_item",
                    )
                    yield Static(
                        f"🏠 Local Address: {self.connection_data['laddr']}",
                        classes="detail_item",
                        markup=False,
                    )
                    yield Static(
                        f"🌐 Remote Address: {self.connection_data['raddr']}",
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
                        yield Static("🔧 Process Details", classes="detail_title")
                        yield Static(
                            f"📁 Executable: {self.process_info.get('exe', 'N/A')}",
                            classes="detail_item",
                        )
                        yield Static(
                            f"💻 Command Line: {self.process_info.get('cmd', 'N/A')}",
                            classes="detail_item",
                        )
                        yield Static(
                            f"📊 Status: {self.process_info.get('status', 'N/A')}",
                            classes="detail_item",
                        )
                        yield Static(
                            f"👤 User: {self.process_info.get('username', 'N/A')}",
                            classes="detail_item",
                        )
                        yield Static(
                            f"📂 Working Directory: {self.process_info.get('cwd', 'N/A')}",
                            classes="detail_item",
                        )
                        yield Static(
                            f"🧵 Threads: {self.process_info.get('num_threads', 'N/A')}",
                            classes="detail_item",
                        )

                        cpu_percent = self.process_info.get("cpu_percent", 0.0)
                        cpu_icon = (
                            "🔥"
                            if cpu_percent > 50
                            else "⚡" if cpu_percent > 10 else "💤"
                        )
                        yield Static(
                            f"{cpu_icon} CPU Usage: {cpu_percent:.1f}%",
                            classes="detail_item",
                        )

                        memory_percent = self.process_info.get("memory_percent", 0.0)
                        memory_display = (
                            f"{memory_percent:.2f}%"
                            if isinstance(memory_percent, (int, float))
                            else "N/A"
                        )
                        memory_icon = (
                            "🚨"
                            if memory_percent > 80
                            else "⚠️" if memory_percent > 50 else "💾"
                        )
                        yield Static(
                            f"{memory_icon} Memory Usage: {memory_display}",
                            classes="detail_item",
                        )

                        # Network connections from this process
                        connections = self.process_info.get("connections", [])
                        if connections:
                            conn_count = (
                                len(connections) if isinstance(connections, list) else 0
                            )
                            yield Static(
                                f"🌐 Active Connections: {conn_count}",
                                classes="detail_item",
                            )

            with Container(id="button_container"):
                yield Button("🔙 Back to Connections", id="back_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "back_button":
            self.app.pop_screen()


class NetshowApp(App):
    """A modern real‑time network connection monitor with enhanced visuals.

    Features:
    • **Beautiful gradient UI** with glass morphism effects
    • **Animated status indicators** and visual feedback
    • **Enhanced typography** with semantic icons
    • **Preserves scroll position** when the table refreshes
    • **Process-aware monitoring** with detailed drill-down views
    • **Responsive design** that adapts to terminal size
    """

    CSS = CSS

    total_connections = reactive(0)
    active_connections = reactive(0)
    listening_connections = reactive(0)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            with Container(id="stats_container"):
                yield Static("🔄 Initializing NetShow…", id="status_bar")
            yield DataTable(id="connections_table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#connections_table", DataTable)
        table.add_columns(
            "🆔 PID",
            "🔖 Service",
            "⚙️  Process",
            "🏠 Local Address",
            "🌐 Remote Address",
            "📊 Status",
        )

        # Enable cursor to allow row selection
        table.cursor_type = "row"
        table.can_focus = True

        # Refresh at regular intervals
        self.timer: Timer = self.set_interval(
            REFRESH_INTERVAL, self.refresh_connections
        )
        self.refresh_connections()

    def refresh_connections(self) -> None:
        table = self.query_one("#connections_table", DataTable)

        # Capture current scroll offset & cursor row
        row_offset, col_offset = getattr(table, "scroll_offset", (0, 0))
        cursor_row = getattr(table, "cursor_row", 0)

        table.clear()

        status_bar = self.query_one("#status_bar", Static)
        using_root = os.geteuid() == 0

        try:
            conns = get_psutil_conns() if using_root else get_lsof_conns()
        except (psutil.AccessDenied, PermissionError):
            conns = get_lsof_conns()
            using_root = False

        # Count connection types for stats
        established = listening = 0
        for c in conns:
            status = c["status"]
            if status == "ESTABLISHED":
                established += 1
            elif status == "LISTEN":
                listening += 1

            # Add status icon to status column
            status_icon = self._get_status_icon(status)
            table.add_row(
                c["pid"],
                c["friendly"],
                c["proc"],
                c["laddr"],
                c["raddr"],
                f"{status_icon} {status}",
            )

        # Update reactive stats
        self.total_connections = len(conns)
        self.active_connections = established
        self.listening_connections = listening

        # Restore scroll & cursor
        if hasattr(table, "scroll_to"):
            table.scroll_to(row_offset, col_offset)
        if cursor_row < table.row_count and hasattr(table, "cursor_coordinate"):
            table.cursor_coordinate = (cursor_row, 0)  # type: ignore

        source = "🔑 psutil (root)" if using_root else "🔧 lsof"
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_bar.update(
            f"📊 Total: {len(conns)} | ✅ Active: {established} | 👂 Listening: {listening} | "
            f"{source} | 🕒 {timestamp}"
        )

    def _get_status_icon(self, status: str) -> str:
        """Get an appropriate icon for connection status."""
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

    async def on_key(self, event: events.Key) -> None:
        if event.key == "q":
            await self.action_quit()
        elif event.key == "enter":
            # When Enter is pressed on a highlighted row
            table = self.query_one("#connections_table", DataTable)
            if table.cursor_row is not None and table.cursor_row < table.row_count:
                # Pause refreshing while viewing details
                self.timer.pause()

                # Get the row data at cursor position and use it directly
                row_data = table.get_row_at(table.cursor_row)
                selected_data = self._get_selected_connection_data(tuple(row_data))
                await self.push_screen(ConnectionDetailScreen(selected_data))

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


if __name__ == "__main__":
    NetshowApp().run()
