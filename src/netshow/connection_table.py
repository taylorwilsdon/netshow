"""Incremental table updates with selection anchored to connection identity."""

from dataclasses import dataclass

from rich.text import Text
from textual.widgets import DataTable

from .models import Connection
from .presentation import STATUS_ICONS, address, literal


@dataclass(frozen=True)
class ProcessCell:
    connection: Connection

    def __rich__(self) -> str:
        return str(self.connection.pid) if self.connection.pid is not None else "—"


class ConnectionTable(DataTable[Text | ProcessCell]):
    HELP = "Select a connection with the arrow keys. Enter opens details; k offers process termination."

    def __init__(self) -> None:
        super().__init__(id="connections_table", cursor_type="row", zebra_stripes=True)
        self.records: dict[str, Connection] = {}
        self.rendered: dict[str, tuple[Text | ProcessCell, ...]] = {}
        self.order: list[str] = []

    def on_mount(self) -> None:
        for key, label, width in (
            ("pid", "PID", 7),
            ("friendly", "Service", 22),
            ("process", "Process", 16),
            ("local", "Local address", 22),
            ("remote", "Remote address", 22),
            ("status", "Status", 14),
        ):
            self.add_column(label, key=key, width=width)

    @property
    def selected(self) -> Connection | None:
        if not self.row_count:
            return None
        row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
        return self.records.get(str(row_key.value))

    def display_connections(
        self, connections: list[Connection], emojis: bool, expanded: bool
    ) -> None:
        selected = self.selected
        old_cursor = self.cursor_row
        offset = self.scroll_offset
        records = {c.key: c for c in connections}
        order = list(records)
        columns = ("pid", "friendly", "process", "local", "remote", "status")
        with self.app.batch_update():
            for key in self.records.keys() - records.keys():
                self.remove_row(key)
                self.rendered.pop(key, None)
            for key, connection in records.items():
                icon = STATUS_ICONS.get(connection.status, "·") + " " if emojis else ""
                row: tuple[Text | ProcessCell, ...] = (
                    ProcessCell(connection),
                    Text(literal(connection.friendly)),
                    Text(literal(connection.process)),
                    Text(literal(address(connection.local, expanded))),
                    Text(literal(address(connection.remote, expanded))),
                    Text(icon + literal(connection.status)),
                )
                if key not in self.records:
                    self.add_row(*row, key=key)
                else:
                    for column, old, new in zip(columns, self.rendered[key], row, strict=True):
                        if old != new:
                            self.update_cell(key, column, new)
                self.rendered[key] = row
            if order != self.order:
                ranks = {key: index for index, key in enumerate(order)}
                self.sort("pid", key=lambda cell: ranks[cell.connection.key])
            self.records = records
            self.order = order
            if order:
                index = (
                    self.get_row_index(selected.key)
                    if selected and selected.key in records
                    else min(old_cursor, len(order) - 1)
                )
                self.move_cursor(row=index, animate=False, scroll=False)
            self.scroll_to(x=offset.x, y=offset.y, animate=False, force=True)
