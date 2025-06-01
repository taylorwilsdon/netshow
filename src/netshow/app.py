import os

import psutil
from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Button, DataTable, Footer, Header, Static

from .helpers import get_lsof_conns, get_psutil_conns
from .styles import CSS


class ConnectionDetailScreen(Screen):
    """Screen for displaying detailed information about a selected connection."""

    BINDINGS = [("escape", "app.pop_screen", "Back to connections")]

    def __init__(self, connection_data: dict):
        super().__init__()
        self.connection_data = connection_data
        self.process_info = {}

        # Try to get additional process info if PID is available
        try:
            if connection_data["pid"] != "-":
                pid = int(connection_data["pid"])
                proc = psutil.Process(pid)
                self.process_info = {
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
            pass

    def compose(self) -> ComposeResult:
        """Compose the detail screen layout."""
        yield Header(show_clock=True)

        with ScrollableContainer():
            yield Static(
                f"Connection Details: {self.connection_data['friendly']}", id="detail_title"
            )

            with Container(id="connection_details"):
                yield Static(f"PID: {self.connection_data['pid']}", classes="detail_item")
                yield Static(f"Process: {self.connection_data['proc']}", classes="detail_item")
                yield Static(
                    f"Friendly Name: {self.connection_data['friendly']}", classes="detail_item"
                )
                yield Static(
                    f"Local Address: {self.connection_data['laddr']}", classes="detail_item", markup=False
                )
                yield Static(
                    f"Remote Address: {self.connection_data['raddr']}", classes="detail_item", markup=False
                )
                yield Static(f"Status: {self.connection_data['status']}", classes="detail_item")

            # Show additional process info if available
            if self.process_info:
                yield Static("Process Information", id="process_info_title")

                with Container(id="process_info"):
                    yield Static(
                        f"Executable: {self.process_info.get('exe', 'N/A')}", classes="detail_item"
                    )
                    yield Static(
                        f"Command Line: {self.process_info.get('cmd', 'N/A')}",
                        classes="detail_item",
                    )
                    yield Static(
                        f"Status: {self.process_info.get('status', 'N/A')}", classes="detail_item"
                    )
                    yield Static(
                        f"User: {self.process_info.get('username', 'N/A')}", classes="detail_item"
                    )
                    yield Static(
                        f"Working Directory: {self.process_info.get('cwd', 'N/A')}",
                        classes="detail_item",
                    )
                    yield Static(
                        f"Threads: {self.process_info.get('num_threads', 'N/A')}",
                        classes="detail_item",
                    )
                    yield Static(
                        f"CPU Usage: {self.process_info.get('cpu_percent', 'N/A')}%",
                        classes="detail_item",
                    )
                    memory_pct = round(self.process_info.get("memory_percent", 0), 2)
                    yield Static(f"Memory Usage: {memory_pct}%", classes="detail_item")

                    # Network connections from this process
                    if self.process_info.get("connections"):
                        conn_count = len(self.process_info.get("connections", []))
                        yield Static(f"Active Connections: {conn_count}", classes="detail_item")

            yield Button("Back to Connections", id="back_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "back_button":
            self.app.pop_screen()


class NetTopApp(App):
    """A real‑time network connection monitor with friendly service names.

    Tweaks in this revision:
    • **Preserves scroll position** when the table refreshes.
    • Reduces refresh rate to once every 3 seconds for stability.
    • Retains the selenized‑dark full‑width theme.
    • Added ability to view detailed connection information by clicking on rows.
    """

    CSS = CSS

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            yield Static("Initializing…", id="status_bar")
            yield DataTable(id="connections_table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#connections_table", DataTable)
        table.add_columns("PID", "Service", "Process", "Local Address", "Remote Address", "Status")

        # Enable cursor to allow row selection
        table.cursor_type = "row"
        table.can_focus = True

        # Refresh every 3 seconds (was 1s)
        self.timer: Timer = self.set_interval(3.0, self.refresh_connections)
        self.refresh_connections()

    def refresh_connections(self) -> None:
        table = self.query_one("#connections_table", DataTable)

        # Capture current scroll offset & cursor row
        try:
            row_offset, col_offset = table.scroll_offset
        except AttributeError:
            row_offset, col_offset = 0, 0
        cursor_row = getattr(table, "cursor_row", 0)

        table.clear()

        status_bar = self.query_one("#status_bar", Static)
        using_root = os.geteuid() == 0

        try:
            conns = get_psutil_conns() if using_root else get_lsof_conns()
        except (psutil.AccessDenied, PermissionError):
            conns = get_lsof_conns()
            using_root = False

        for c in conns:
            table.add_row(c["pid"], c["friendly"], c["proc"], c["laddr"], c["raddr"], c["status"])

        # Restore scroll & cursor
        try:
            table.scroll_to(row_offset, col_offset)
            if cursor_row < table.row_count:
                table.cursor_coordinate = (cursor_row, 0)
        except Exception:
            pass

        source = "psutil (root)" if using_root else "lsof"
        status_bar.update(f"Connections: {len(conns)} | Source: {source}")

    async def on_key(self, event: events.Key) -> None:
        if event.key == "q":
            await self.action_quit()
        elif event.key == "enter":
            # When Enter is pressed on a highlighted row
            table = self.query_one("#connections_table", DataTable)
            if table.cursor_row is not None and table.cursor_row < table.row_count:
                # Get the row key at cursor position
                row_key = table.get_row_at(table.cursor_row)[0]
                await self.show_connection_details(row_key)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row highlighting in the DataTable."""
        # This event fires when cursor moves over rows
        pass

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the DataTable."""
        await self.show_connection_details(event.row_key)

    async def show_connection_details(self, row_key) -> None:
        """Show connection details for the selected row."""
        # Pause refreshing while viewing details
        self.timer.pause()

        # Get the selected row's data
        table = self.query_one("#connections_table", DataTable)
        selected_data = {}

        # Extract all data from the table row
        row_data = table.get_row(row_key)
        columns = ["pid", "friendly", "proc", "laddr", "raddr", "status"]
        selected_data = dict(zip(columns, row_data))

        # Push the detail screen
        await self.push_screen(ConnectionDetailScreen(selected_data))

    async def on_screen_resume(self) -> None:
        """Called when this screen is resumed (after popping another screen)."""
        # Resume refreshing when returning from detail view
        self.timer.resume()
        self.refresh_connections()


if __name__ == "__main__":
    NetTopApp().run()
