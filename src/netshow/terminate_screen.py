"""Explicit confirmation and separately confirmed force termination."""

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from .models import Connection, ProcessDetails
from .presentation import literal
from .processes import ProcessInspector, ProcessOutcome, control_unavailable, signal_process


class TerminateScreen(ModalScreen[None]):
    BINDINGS = [("escape", "cancel", "Cancel")]

    class Inspected(Message):
        def __init__(self, details: ProcessDetails) -> None:
            super().__init__()
            self.details = details

    class Completed(Message):
        def __init__(self, outcome: ProcessOutcome) -> None:
            super().__init__()
            self.outcome = outcome

    def __init__(self, connection: Connection) -> None:
        super().__init__()
        self.connection = connection
        self.busy = False
        self.force = False

    def compose(self) -> ComposeResult:
        with Vertical(id="terminate_dialog"):
            yield Static("Terminate process?", id="terminate_title", classes="section_title")
            with VerticalScroll():
                yield Static(
                    literal(
                        f"{self.connection.friendly} · PID {self.connection.pid}\nInspecting process…"
                    ),
                    id="terminate_identity",
                    markup=False,
                )
                yield Static(
                    "This affects all connections owned by this process. Unsaved work may be lost.",
                    classes="dialog_explanation",
                )
                yield Static("", id="terminate_status", markup=False)
            with Horizontal(classes="dialog_buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Terminate", id="confirm", variant="error", disabled=True)

    def on_mount(self) -> None:
        self.query_one("#cancel", Button).focus()
        self.inspect_process()

    @work(thread=True, exit_on_error=False)
    def inspect_process(self) -> None:
        self.post_message(self.Inspected(ProcessInspector(self.connection.identity).sample()))

    def on_terminate_screen_inspected(self, message: Inspected) -> None:
        details = message.details
        fields = dict(details.fields)
        text = (
            f"{self.connection.friendly} · PID {self.connection.pid}\n"
            f"Owner: {fields.get('Owner', 'Unavailable')}\n"
            f"Executable: {fields.get('Executable', 'Unavailable')}"
        )
        self.query_one("#terminate_identity", Static).update(literal(text))
        reason = control_unavailable(self.connection.identity) or details.error
        self.query_one("#terminate_status", Static).update(
            reason or "Send a graceful termination request."
        )
        self.query_one("#confirm", Button).disabled = reason is not None

    def action_cancel(self) -> None:
        if not self.busy:
            self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.action_cancel()
        elif event.button.id == "confirm" and not self.busy:
            self.busy = True
            self.query_one("#confirm", Button).disabled = True
            self.query_one("#cancel", Button).disabled = True
            self.query_one("#terminate_status", Static).update("Waiting for process exit…")
            self.send_signal(self.force)

    @work(thread=True, exit_on_error=False)
    def send_signal(self, force: bool) -> None:
        identity = self.connection.identity
        if identity is not None:
            self.post_message(self.Completed(signal_process(identity, force=force)))

    def on_terminate_screen_completed(self, message: Completed) -> None:
        self.busy = False
        outcome = message.outcome
        self.query_one("#terminate_status", Static).update(literal(outcome.message))
        cancel = self.query_one("#cancel", Button)
        cancel.disabled = False
        cancel.focus()
        if outcome.state == "exited":
            self.notify(outcome.message)
            self.dismiss(None)
        elif outcome.state == "alive" and not self.force:
            self.force = True
            self.query_one("#terminate_title", Static).update("Force kill process?")
            self.query_one("#terminate_status", Static).update(
                outcome.message + "\nForce kill stops it immediately without allowing cleanup."
            )
            confirm = self.query_one("#confirm", Button)
            confirm.label = "Force kill"
            confirm.disabled = False
        else:
            cancel.label = "Close"
