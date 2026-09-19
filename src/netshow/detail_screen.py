"""Responsive process inspection with a CPU baseline that survives refreshes."""

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Button, Footer, Header, Static

from .models import Connection, ProcessDetails
from .presentation import literal
from .processes import ProcessInspector, control_unavailable
from .terminate_screen import TerminateScreen


class DetailFields(Vertical):
    """Aligned labels and wrapping values that can update without rebuilding the view."""

    def __init__(self, fields: tuple[tuple[str, str], ...], *, id: str) -> None:
        super().__init__(id=id)
        self.fields = fields

    def compose(self) -> ComposeResult:
        for index, (label, value) in enumerate(self.fields):
            with Horizontal(classes="detail_field"):
                yield Static(label, classes="detail_label", markup=False)
                yield Static(
                    literal(value), id=f"value_{index}", classes="detail_value", markup=False
                )

    def update_values(self, fields: tuple[tuple[str, str], ...]) -> None:
        values = dict(fields)
        for index, (label, _) in enumerate(self.fields):
            self.query_one(f"#value_{index}", Static).update(literal(values.get(label, "—")))


class ConnectionDetailScreen(Screen[None]):
    BINDINGS = [
        ("escape,left", "back", "Back"),
        ("k", "terminate", "Terminate process"),
        ("ctrl+r", "refresh", "Refresh"),
    ]

    class Inspected(Message):
        def __init__(self, details: ProcessDetails) -> None:
            super().__init__()
            self.details = details

    def __init__(self, connection: Connection) -> None:
        super().__init__()
        self.connection = connection
        self.inspector = ProcessInspector(connection.identity)
        self.timer: Timer | None = None
        self.busy = False
        self.active = False
        self.process_error: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="detail_scroll"):
            with Vertical(id="detail_content"):
                yield Static(literal(self.connection.friendly), id="detail_title", markup=False)
                with Horizontal(id="detail_panels"):
                    with Vertical(id="connection_panel", classes="detail_panel"):
                        yield Static("Connection", classes="section_title")
                        yield DetailFields(
                            (
                                ("PID", str(self.connection.pid or "Unavailable")),
                                ("Process", self.connection.process),
                                ("Local", self.connection.local),
                                ("Remote", self.connection.remote or "—"),
                                ("Status", self.connection.status),
                            ),
                            id="connection_info",
                        )
                    with Vertical(id="process_panel", classes="detail_panel"):
                        yield Static("Process", classes="section_title")
                        yield Static("Loading process details…", id="process_status", markup=False)
                        yield DetailFields(
                            tuple(
                                (label, "—")
                                for label in (
                                    "Name",
                                    "Owner",
                                    "Executable",
                                    "Working directory",
                                    "Command",
                                    "Status",
                                    "Threads",
                                    "Memory",
                                    "CPU",
                                )
                            ),
                            id="process_info",
                        )
        with Horizontal(id="detail_buttons"):
            yield Button("Back to connections", id="back", variant="primary")
            yield Button(
                "Terminate process…",
                id="terminate",
                variant="error",
                disabled=control_unavailable(self.connection.identity) is not None,
            )
        yield Footer()

    def on_mount(self) -> None:
        self.set_class(self.size.width < 100, "compact")
        self.timer = self.set_interval(1, self.action_refresh)
        self.active = True
        self.action_refresh()

    def on_resize(self) -> None:
        self.set_class(self.size.width < 100, "compact")

    def on_screen_resume(self) -> None:
        self.active = True
        if self.timer:
            self.timer.resume()
            self.action_refresh()

    def on_screen_suspend(self) -> None:
        self.active = False
        if self.timer:
            self.timer.pause()

    def action_refresh(self) -> None:
        if self.active and not self.busy:
            self.busy = True
            self.inspect_process()

    @work(thread=True, exit_on_error=False)
    def inspect_process(self) -> None:
        self.post_message(self.Inspected(self.inspector.sample()))

    def on_connection_detail_screen_inspected(self, message: Inspected) -> None:
        self.busy = False
        self.process_error = message.details.error
        status = self.query_one("#process_status", Static)
        status.display = self.process_error is not None
        status.update(literal(self.process_error or ""))
        info = self.query_one("#process_info", DetailFields)
        info.display = self.process_error is None
        info.update_values(message.details.fields)
        self.query_one("#terminate", Button).disabled = bool(
            self.process_error or control_unavailable(self.connection.identity)
        )
        self.refresh_bindings()

    def action_back(self) -> None:
        self.dismiss(None)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "terminate":
            return (
                self.process_error is None and control_unavailable(self.connection.identity) is None
            )
        return True

    def action_terminate(self) -> None:
        if self.check_action("terminate", ()):
            self.app.push_screen(TerminateScreen(self.connection))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.action_back()
        elif event.button.id == "terminate":
            self.action_terminate()
