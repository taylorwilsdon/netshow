import threading
from dataclasses import replace
from unittest.mock import Mock

import pytest
from textual.widgets import Button, Input, Sparkline, Static

from netshow.app import NetshowApp
from netshow.connection_table import ConnectionTable
from netshow.detail_screen import ConnectionDetailScreen
from netshow.models import CollectionResult, Connection, ProcessDetails, ProcessIdentity
from netshow.processes import ProcessOutcome
from netshow.terminate_screen import TerminateScreen


@pytest.fixture
def records():
    return [
        Connection(222, "server", "Zebra", "[::1]:8080", "", "LISTEN", ProcessIdentity(222, 1), 7),
        Connection(
            333,
            "client",
            "[bold]Alpha[/bold]",
            "127.0.0.1:5000",
            "1.1.1.1:443",
            "ESTABLISHED",
            ProcessIdentity(333, 2),
            8,
        ),
    ]


@pytest.fixture(autouse=True)
def fake_inspection(monkeypatch):
    monkeypatch.setattr(
        "netshow.processes.ProcessInspector.sample",
        lambda self: ProcessDetails(
            self.identity,
            (("Name", "[bold]literal[/bold]"), ("Owner", "test"), ("Executable", "/tmp/test")),
        ),
    )


async def settled(pilot, predicate):
    for _ in range(100):
        await pilot.pause(0.01)
        if predicate():
            return
    assert predicate(), "UI did not reach expected state"


async def test_details_preserve_ipv6_and_resume_refresh(records):
    collector = Mock(return_value=CollectionResult(tuple(records)))
    app = NetshowApp(collector=collector)
    async with app.run_test() as pilot:
        await settled(pilot, lambda: app.connections.last_success is not None)
        await pilot.press("enter")
        assert isinstance(app.screen, ConnectionDetailScreen)
        assert app.screen.connection.local == "[::1]:8080"
        await pilot.pause()
        assert not app.connections.active
        count = collector.call_count
        await pilot.press("escape")
        await settled(pilot, lambda: collector.call_count > count)
        assert app.connections.active
        count = collector.call_count
        await pilot.press("ctrl+r")
        await settled(pilot, lambda: collector.call_count > count)


async def test_selection_survives_updates_sort_and_reordering(records):
    collector = Mock(return_value=CollectionResult(tuple(records)))
    app = NetshowApp(collector=collector)
    async with app.run_test() as pilot:
        await settled(pilot, lambda: app.connections.last_success is not None)
        table = app.connections.query_one(ConnectionTable)
        await pilot.press("down", "p")
        assert table.selected.pid == 333
        assert table.cursor_row == 0
        collector.return_value = CollectionResult(
            (replace(records[0], status="CLOSE_WAIT"), records[1])
        )
        await pilot.press("ctrl+r")
        await settled(pilot, lambda: app.connections.snapshot[0].status == "CLOSE_WAIT")
        assert table.selected.pid == 333
        await pilot.press("p")
        assert table.selected.pid == 333
        assert table.cursor_row == 1
        collector.return_value = CollectionResult((records[0],))
        await pilot.press("ctrl+r")
        await settled(pilot, lambda: table.row_count == 1)
        assert table.selected.pid == 222


async def test_filter_typing_shortcuts_literal_regex_and_clear(records):
    collector = Mock(return_value=CollectionResult(tuple(records)))
    app = NetshowApp(collector=collector)
    async with app.run_test() as pilot:
        await settled(pilot, lambda: app.connections.last_success is not None)
        calls = collector.call_count
        await pilot.press("/")
        field = app.connections.query_one(Input)
        await pilot.press("p", "s", "i", "e", "v", "k", "f")
        assert field.value == "psievkf"
        assert app.connections.sort_mode == "default"
        assert app.screen is app.connections
        field.value = "["
        await pilot.pause(0.2)
        assert app.connections.invalid_regex
        assert len(app.connections.filtered_connections) == 2
        assert collector.call_count == calls
        field.value = "333"
        await pilot.pause(0.2)
        assert app.connections.query_one(ConnectionTable).selected.pid == 333
        await pilot.press("escape")
        assert not field.display
        await pilot.press("/")
        field.value = ""
        await pilot.pause(0.2)
        assert app.connections.query_one(ConnectionTable).row_count == 2


async def test_slow_collection_coalesces_and_discards_suspended_result(records):
    release = threading.Event()
    entered = threading.Event()
    count = 0

    def collector():
        nonlocal count
        count += 1
        if count == 1:
            entered.set()
            assert release.wait(3)
            return CollectionResult((records[0],))
        return CollectionResult((records[1],))

    app = NetshowApp(collector=collector)
    try:
        async with app.run_test() as pilot:
            await settled(pilot, entered.is_set)
            for _ in range(10):
                app.connections.action_refresh()
            await pilot.press("/")
            assert isinstance(app.focused, Input)
            assert count == 1
            app.push_screen(ConnectionDetailScreen(records[0]))
            await pilot.pause()
            release.set()
            await settled(pilot, lambda: not app.connections.collecting)
            assert app.connections.last_success is None
            await pilot.press("escape")
            await settled(pilot, lambda: app.connections.last_success is not None)
            assert count == 2
            assert app.connections.snapshot == (records[1],)
    finally:
        release.set()


async def test_stale_snapshot_survives_failure(records):
    collector = Mock(return_value=CollectionResult(tuple(records), "lsof", limited=True))
    app = NetshowApp(collector=collector)
    async with app.run_test() as pilot:
        await settled(pilot, lambda: app.connections.last_success is not None)
        collector.return_value = CollectionResult(error="lsof timed out")
        await pilot.press("ctrl+r")
        await settled(pilot, lambda: app.connections.result.error is not None)
        assert app.connections.snapshot == tuple(records)
        assert app.connections.query_one(ConnectionTable).row_count == 2
        assert "Stale data" in str(app.connections.query_one("#collection_status", Static).content)


@pytest.mark.parametrize("size", [(60, 20), (80, 24), (120, 40)])
async def test_layout_themes_and_symbols(size, records):
    app = NetshowApp(collector=lambda: CollectionResult(tuple(records)))
    async with app.run_test(size=size) as pilot:
        await settled(pilot, lambda: app.connections.last_success is not None)
        assert app.connections.query_one(Sparkline).display == (size[0] >= 80)
        for theme in ["solarized-light", "ansi-dark", "ansi-light"]:
            app.theme = theme
            await pilot.pause()
        await pilot.press("e", "v")
        assert not app.connections.show_emojis
        assert app.connections.expand_ipv6
        await pilot.press("enter")
        await pilot.pause()
        assert app.screen.has_class("compact") == (size[0] < 100)
        await pilot.press("k")
        await settled(pilot, lambda: not app.screen.query_one("#confirm", Button).disabled)
        assert app.screen.query_one("#cancel", Button).region.bottom <= size[1]
        assert app.screen.query_one("#confirm", Button).region.right <= size[0]


async def test_termination_cancel_and_separate_force(records, monkeypatch):
    signal = Mock(
        side_effect=[ProcessOutcome("alive", "Still running"), ProcessOutcome("exited", "Exited")]
    )
    monkeypatch.setattr("netshow.terminate_screen.signal_process", signal)
    app = NetshowApp(collector=lambda: CollectionResult(tuple(records)))
    async with app.run_test() as pilot:
        await settled(pilot, lambda: app.connections.last_success is not None)
        await pilot.press("k")
        await settled(pilot, lambda: not app.screen.query_one("#confirm", Button).disabled)
        assert app.focused.id == "cancel"
        await pilot.press("enter")
        assert app.screen is app.connections
        signal.assert_not_called()
        await pilot.press("k")
        await settled(pilot, lambda: not app.screen.query_one("#confirm", Button).disabled)
        await pilot.click("#confirm")
        await settled(pilot, lambda: app.screen.force)
        assert signal.call_count == 1
        assert app.focused.id == "cancel"
        await pilot.pause(0.35)  # Let Textual’s button press animation finish.
        await pilot.click("#confirm")
        await settled(pilot, lambda: app.screen is app.connections)
        assert signal.call_args_list[0].kwargs == {"force": False}
        assert signal.call_args_list[1].kwargs == {"force": True}


async def test_no_duplicate_signals(records, monkeypatch):
    release = threading.Event()
    signal = Mock(
        side_effect=lambda *args, **kwargs: (
            release.wait(3),
            ProcessOutcome("denied", "Permission denied"),
        )[1]
    )
    monkeypatch.setattr("netshow.terminate_screen.signal_process", signal)
    app = NetshowApp(collector=lambda: CollectionResult(tuple(records)))
    try:
        async with app.run_test() as pilot:
            await settled(pilot, lambda: app.connections.last_success is not None)
            await pilot.press("k")
            await settled(pilot, lambda: not app.screen.query_one("#confirm", Button).disabled)
            await pilot.click("#confirm")
            await settled(pilot, lambda: signal.call_count == 1)
            await pilot.press("enter", "enter", "escape")
            assert isinstance(app.screen, TerminateScreen)
            assert app.screen.busy
            assert signal.call_count == 1
            release.set()
            await settled(pilot, lambda: not app.screen.busy)
            assert app.screen.query_one("#confirm", Button).disabled
            assert app.focused.id == "cancel"
    finally:
        release.set()


async def test_large_table_updates_incrementally(records, monkeypatch):
    fixture = tuple(replace(records[0], pid=10000 + i, fd=i) for i in range(5000))
    app = NetshowApp(collector=lambda: CollectionResult(fixture))
    async with app.run_test(size=(120, 40)) as pilot:
        await settled(pilot, lambda: app.connections.last_success is not None)
        table = app.connections.query_one(ConnectionTable)
        assert table.row_count == 5000
        clear = Mock(side_effect=AssertionError("Unexpected full table rebuild"))
        monkeypatch.setattr(table, "clear", clear)
        update = Mock(wraps=table.update_cell)
        monkeypatch.setattr(table, "update_cell", update)
        app.connections.snapshot = (replace(fixture[0], status="CLOSE_WAIT"), *fixture[1:])
        app.connections.render_connections()
        assert update.call_count == 2  # PID cell carries the model, plus changed status.
        await pilot.press("down", "/")
        assert isinstance(app.focused, Input)
        assert table.cursor_row == 1
        clear.assert_not_called()
