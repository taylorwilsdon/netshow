import psutil
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.screen import Screen
from textual.widgets import Button, Header, Static

from .types_and_constants import ConnectionData


class ConnectionDetailScreen(Screen):
    """Screen for displaying detailed information about a selected connection."""

    BINDINGS = [("escape", "app.pop_screen", "Back to connections")]

    def __init__(self, connection_data: ConnectionData):
        super().__init__()
        self.connection_data = connection_data
        self.proc = None
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
            if self.proc is None:
                self.proc = psutil.Process(pid)
                self.proc.cpu_percent()  # Initialize CPU percent baseline
            return {
                "name": self.proc.name(),
                "exe": self.proc.exe(),
                "cmd": " ".join(self.proc.cmdline()),
                "create_time": self.proc.create_time(),
                "status": self.proc.status(),
                "username": self.proc.username(),
                "cwd": self.proc.cwd(),
                "num_threads": self.proc.num_threads(),
                "cpu_percent": self.proc.cpu_percent(),
                "memory_percent": self.proc.memory_percent(),
                "open_files": self.proc.open_files(),
                "connections": self.proc.connections(),
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