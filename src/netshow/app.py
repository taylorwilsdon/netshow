"""Application shell and connection screen; workers own system I/O."""

import logging
import time
from collections.abc import Callable, Iterable, Sequence

from textual import work
from textual.app import App, ComposeResult, SystemCommand
from textual.containers import Grid, Vertical
from textual.filter import LineFilter, Monochrome
from textual.message import Message
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Footer, Header, Input, Sparkline, Static

from .bandwidth import BandwidthSampler
from .collectors import collect_connections
from .connection_table import ConnectionTable
from .detail_screen import ConnectionDetailScreen
from .models import BandwidthSample, CollectionResult, Connection
from .presentation import format_bytes, literal, select_connections
from .processes import control_unavailable
from .terminate_screen import TerminateScreen
from .theme import SELENIZED_DARK

log = logging.getLogger(__name__)


class ConnectionsScreen(Screen[None]):
    BINDINGS = [
        ("ctrl+r", "refresh", "Refresh"),
        ("/", "search", "Search"),
        ("f", "toggle_filter", "Filter"),
        ("s", "sort_status", "Sort status"),
        ("p", "sort_process", "Sort process"),
        ("i", "interface", "Interface"),
        ("e", "emojis", "Symbols"),
        ("v", "ipv6", "IPv6"),
        ("k", "terminate", "Terminate"),
        ("escape", "close_filter", "Close filter"),
    ]

    class Collected(Message):
        def __init__(self, generation: int, result: CollectionResult) -> None:
            super().__init__()
            self.generation, self.result = generation, result

    class Sampled(Message):
        def __init__(
            self, sample: BandwidthSample, history: tuple[float, ...], interfaces: list[str]
        ) -> None:
            super().__init__()
            self.sample, self.history, self.interfaces = sample, history, interfaces

    def __init__(self, interval: float, collector: Callable[[], CollectionResult]) -> None:
        super().__init__()
        self.interval, self.collector = interval, collector
        self.snapshot: tuple[Connection, ...] = ()
        self.result = CollectionResult()
        self.filtered_connections: list[Connection] = []
        self.sort_mode = "default"
        self.show_emojis = True
        self.expand_ipv6 = False
        self.query_text = ""
        self.invalid_regex = False
        self.generation = 0
        self.collecting = False
        self.pending = False
        self.active = False
        self.last_success: float | None = None
        self.timer: Timer | None = None
        self.bandwidth_timer: Timer | None = None
        self.debounce: Timer | None = None
        self.sampler = BandwidthSampler()
        self.sampling = False
        self.sample = BandwidthSample(available=False)
        self.interfaces = ["all"]
        self.selected_interface = "all"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="metrics"):
            with Grid(id="counts"):
                for widget_id in ("total", "active", "listening", "bandwidth"):
                    yield Static("—", id=widget_id, classes="metric", markup=False)
            yield Sparkline([], id="bandwidth_spark")
        yield Input(placeholder="Filter by PID, service, address, or status (regex)", id="filter")
        yield Static("Collecting connections…", id="collection_status", markup=False)
        yield Static("", id="empty_state", markup=False)
        yield ConnectionTable()
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(Input).display = False
        self.active = True
        self.timer = self.set_interval(self.interval, self.action_refresh)
        self.bandwidth_timer = self.set_interval(0.5, self.sample_bandwidth)
        self.set_interval(1, self.render_status)
        self.action_refresh()
        self.sample_bandwidth()
        self.query_one(ConnectionTable).focus()
        self.on_resize()

    def on_screen_suspend(self) -> None:
        self.active = False
        self.generation += 1
        self.pending = False
        if self.timer:
            self.timer.pause()
        if self.bandwidth_timer:
            self.bandwidth_timer.pause()

    def on_screen_resume(self) -> None:
        self.active = True
        if self.timer:
            self.timer.resume()
            self.action_refresh()
        if self.bandwidth_timer:
            self.bandwidth_timer.resume()
        if self.is_mounted:
            self.query_one(ConnectionTable).focus()

    def action_refresh(self) -> None:
        if not self.active:
            return
        if self.collecting:
            self.pending = True
            return
        self.collecting = True
        self.collect(self.generation)

    @work(thread=True, exit_on_error=False)
    def collect(self, generation: int) -> None:
        try:
            result = self.collector()
        except Exception:
            # One explicit worker boundary: preserve the UI and log unexpected failures.
            log.exception("Unexpected connection collection failure")
            result = CollectionResult(error="Unexpected collection failure; try refreshing.")
        self.post_message(self.Collected(generation, result))

    def on_connections_screen_collected(self, message: Collected) -> None:
        self.collecting = False
        if message.generation == self.generation and self.active:
            self.result = message.result
            if not message.result.error:
                self.snapshot = message.result.connections
                self.last_success = time.monotonic()
            self.render_connections()
        if self.active and (self.pending or message.generation != self.generation):
            self.pending = False
            self.action_refresh()

    def render_connections(self) -> None:
        self.filtered_connections, self.invalid_regex = select_connections(
            self.snapshot, self.query_text, self.sort_mode
        )
        self.query_one(ConnectionTable).display_connections(
            self.filtered_connections, self.show_emojis, self.expand_ipv6
        )
        self.render_metrics()
        self.render_status()
        self.refresh_bindings()

    def render_metrics(self) -> None:
        total = len(self.snapshot)
        count = f"{len(self.filtered_connections)} / {total}" if self.query_text else str(total)
        for widget_id, symbol, label, value in (
            ("total", "📊", "Connections", count),
            ("active", "⚡", "Active", sum(c.status == "ESTABLISHED" for c in self.snapshot)),
            ("listening", "👂", "Listening", sum(c.status == "LISTEN" for c in self.snapshot)),
        ):
            prefix = f"{symbol} " if self.show_emojis else ""
            self.query_one(f"#{widget_id}", Static).update(f"{prefix}{label}: {value}")
        sample = self.sample
        text = (
            f"RX {format_bytes(sample.received)}/s   TX {format_bytes(sample.sent)}/s"
            if sample.available
            else "Bandwidth unavailable"
        )
        bandwidth = self.query_one("#bandwidth", Static)
        prefix = "🔥 " if self.show_emojis else ""
        bandwidth.border_title = literal(f"{prefix}Bandwidth · {sample.interface}")
        bandwidth.update(literal(text))

    def render_status(self) -> None:
        if not self.is_mounted:
            return
        status = "Collecting connections…"
        if self.last_success is not None:
            age = int(time.monotonic() - self.last_success)
            status = f"{self.result.source} · Updated {age}s ago · Sort: {self.sort_mode}"
            if self.result.limited:
                status += " · Limited visibility"
        if self.result.error:
            status = ("Stale data · " if self.last_success is not None else "") + self.result.error
        if self.query_text:
            status += " · Filter active"
        if self.invalid_regex:
            status += " · Invalid regex: matching literal text"
        self.query_one("#collection_status", Static).update(literal(status))
        empty = self.query_one("#empty_state", Static)
        empty.display = not self.filtered_connections
        if self.result.error and self.last_success is None:
            empty.update("Connections unavailable. Press Ctrl+R to retry.")
        elif self.last_success is None:
            empty.update("Loading TCP connections…")
        elif self.query_text:
            empty.update("No connections match this filter.")
        else:
            empty.update("No visible TCP connections.")

    def sample_bandwidth(self) -> None:
        if self.active and not self.sampling:
            self.sampling = True
            self.read_bandwidth(self.selected_interface)

    @work(thread=True, exit_on_error=False)
    def read_bandwidth(self, interface: str) -> None:
        sample = self.sampler.sample(interface)
        self.post_message(
            self.Sampled(sample, tuple(self.sampler.history), list(self.sampler.interfaces))
        )

    def on_connections_screen_sampled(self, message: Sampled) -> None:
        self.sampling = False
        self.interfaces = message.interfaces
        # A user may have switched interfaces while the worker was running.
        if (
            message.sample.interface != self.selected_interface
            and self.selected_interface in self.interfaces
        ):
            return
        self.sample = message.sample
        self.selected_interface = message.sample.interface
        self.query_one(Sparkline).data = message.history
        self.render_metrics()

    def on_resize(self) -> None:
        if self.is_mounted:
            self.set_class(self.size.width < 100, "compact")
            self.query_one(Sparkline).display = self.size.width >= 80

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if not self.is_mounted:
            return False
        if action == "close_filter":
            return self.query_one(Input).display
        if isinstance(self.focused, Input) and action not in ("search", "refresh"):
            return False
        if action == "terminate":
            selected = self.query_one(ConnectionTable).selected
            return selected is not None and control_unavailable(selected.identity) is None
        return True

    def action_search(self) -> None:
        field = self.query_one(Input)
        field.display = True
        field.focus()

    def action_close_filter(self) -> None:
        self.query_one(Input).display = False
        self.query_one(ConnectionTable).focus()

    def action_toggle_filter(self) -> None:
        if self.query_one(Input).display:
            self.action_close_filter()
        else:
            self.action_search()

    def on_input_changed(self, event: Input.Changed) -> None:
        self.query_text = event.value
        if self.debounce:
            self.debounce.stop()
        self.debounce = self.set_timer(0.15, self.render_connections)

    def on_input_submitted(self) -> None:
        self.query_one(ConnectionTable).focus()

    def action_sort_status(self) -> None:
        self.sort_mode = "default" if self.sort_mode == "status" else "status"
        self.render_connections()

    def action_sort_process(self) -> None:
        self.sort_mode = "default" if self.sort_mode == "process" else "process"
        self.render_connections()

    def action_interface(self) -> None:
        index = (
            self.interfaces.index(self.selected_interface)
            if self.selected_interface in self.interfaces
            else 0
        )
        self.selected_interface = self.interfaces[(index + 1) % len(self.interfaces)]
        self.sample_bandwidth()

    def action_emojis(self) -> None:
        self.show_emojis = not self.show_emojis
        self.render_connections()

    def action_ipv6(self) -> None:
        self.expand_ipv6 = not self.expand_ipv6
        self.render_connections()

    def on_data_table_row_highlighted(self) -> None:
        self.refresh_bindings()

    def on_data_table_row_selected(self) -> None:
        selected = self.query_one(ConnectionTable).selected
        if selected:
            self.app.push_screen(ConnectionDetailScreen(selected))

    def action_terminate(self) -> None:
        selected = self.query_one(ConnectionTable).selected
        if selected and control_unavailable(selected.identity) is None:
            self.app.push_screen(TerminateScreen(selected))


class NetshowApp(App[None]):
    CSS_PATH = "netshow.tcss"
    TITLE = "Netshow"
    BINDINGS = [("q", "quit", "Quit"), ("?", "help", "Help")]

    def __init__(
        self,
        interval: float = 3,
        no_colors: bool = False,
        collector: Callable[[], CollectionResult] = collect_connections,
    ) -> None:
        self.no_colors = no_colors
        self.monochrome = Monochrome()
        super().__init__()
        self.register_theme(SELENIZED_DARK)
        self.theme = SELENIZED_DARK.name
        self.connections = ConnectionsScreen(interval, collector)

    def on_mount(self) -> None:
        self.push_screen(self.connections)

    def get_line_filters(self) -> Sequence[LineFilter]:
        filters = list(super().get_line_filters())
        return [*filters, self.monochrome] if self.no_colors else filters

    def action_help(self) -> None:
        if self.screen.query("HelpPanel"):
            self.action_hide_help_panel()
        else:
            self.action_show_help_panel()

    def get_system_commands(self, screen: Screen[object]) -> Iterable[SystemCommand]:
        yield from super().get_system_commands(screen)
        if isinstance(screen, ConnectionsScreen):
            for title, description, action in (
                ("Refresh connections", "Collect a fresh TCP snapshot", screen.action_refresh),
                (
                    "Filter connections",
                    "Search PID, service, address, or status",
                    screen.action_search,
                ),
                ("Sort by process", "Toggle process ordering", screen.action_sort_process),
                ("Sort by status", "Toggle TCP status ordering", screen.action_sort_status),
                ("Network interface", "Cycle the bandwidth interface", screen.action_interface),
                ("Toggle symbols", "Show or hide status symbols", screen.action_emojis),
                ("Expand IPv6", "Toggle full IPv6 addresses", screen.action_ipv6),
            ):
                yield SystemCommand(title, description, action)
        if isinstance(screen, (ConnectionsScreen, ConnectionDetailScreen)) and screen.check_action(
            "terminate", ()
        ):
            yield SystemCommand(
                "Terminate process",
                "Confirm termination of the selected process",
                screen.action_terminate,
            )
