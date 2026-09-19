import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import psutil

from netshow import collectors
from netshow.models import CollectionResult, ProcessIdentity

LSOF = (
    "p123\0cserver with spaces\0\n"
    "f7\0n[::1]:8080\0TST=LISTEN\0\n"
    "f8\0n127.0.0.1:8080->127.0.0.1:50000\0TST=CLOSE_WAIT\0\n"
    "p456\0cclient\0\nf9\0n[fe80::1%lo0]:9000->[::1]:8080\0TST=ESTABLISHED\0\n"
)


def test_lsof_machine_output_preserves_endpoints_and_all_states():
    records = collectors.parse_lsof(LSOF)
    assert len(records) == 3
    assert records[0].process == "server with spaces"
    assert records[0].local == "[::1]:8080"
    assert records[1].status == "CLOSE_WAIT"
    assert records[2].remote == "[::1]:8080"
    assert records[2].fd == 9


def test_lsof_ignores_malformed_records():
    assert collectors.parse_lsof("garbage\0pBAD\0f3\0n*:80\0") == ()


def test_lsof_caches_process_metadata_per_snapshot(monkeypatch):
    run = Mock(return_value=SimpleNamespace(stdout=LSOF, stderr="", returncode=1))
    metadata = Mock(side_effect=lambda pid, name: (name, name, ProcessIdentity(pid, 1)))
    monkeypatch.setattr(collectors.subprocess, "run", run)
    monkeypatch.setattr(collectors, "process_metadata", metadata)
    result = collectors.collect_lsof()
    assert result.error is None
    assert len(result.connections) == 3
    assert metadata.call_count == 2
    assert run.call_args.kwargs["timeout"] == 5
    assert "-sTCP:ESTABLISHED,LISTEN" not in run.call_args.args[0]


def test_lsof_empty_is_not_error(monkeypatch):
    monkeypatch.setattr(
        collectors.subprocess,
        "run",
        Mock(return_value=SimpleNamespace(stdout="", stderr="", returncode=1)),
    )
    assert collectors.collect_lsof().error is None


def test_lsof_reports_errors(monkeypatch):
    for failure, expected in [
        (FileNotFoundError(), "not installed"),
        (subprocess.TimeoutExpired("lsof", 5), "timed out"),
    ]:
        monkeypatch.setattr(collectors.subprocess, "run", Mock(side_effect=failure))
        assert expected in collectors.collect_lsof().error
    for output, stderr in [("malformed", ""), ("", "permission denied")]:
        monkeypatch.setattr(
            collectors.subprocess,
            "run",
            Mock(return_value=SimpleNamespace(stdout=output, stderr=stderr, returncode=1)),
        )
        assert collectors.collect_lsof().error


def test_permission_failure_uses_lsof(monkeypatch):
    monkeypatch.setattr(collectors, "collect_psutil", Mock(side_effect=psutil.AccessDenied()))
    fallback = CollectionResult(source="lsof", limited=True)
    monkeypatch.setattr(collectors, "collect_lsof", Mock(return_value=fallback))
    assert collectors.collect_connections() == fallback


def test_failed_fallback_reports_both_causes(monkeypatch):
    monkeypatch.setattr(collectors, "collect_psutil", Mock(side_effect=psutil.AccessDenied()))
    monkeypatch.setattr(
        collectors,
        "collect_lsof",
        Mock(return_value=CollectionResult(error="missing", source="lsof")),
    )
    assert "psutil access denied; missing" == collectors.collect_connections().error


def test_psutil_retains_unknown_pid_and_caches_metadata(monkeypatch):
    socket = SimpleNamespace(pid=10, laddr=("::1", 80), raddr=(), status="LISTEN", fd=4)
    unknown = SimpleNamespace(
        pid=None, laddr=("127.0.0.1", 80), raddr=(), status="TIME_WAIT", fd=-1
    )
    monkeypatch.setattr(
        collectors.psutil, "net_connections", Mock(return_value=[socket, socket, unknown])
    )
    metadata = Mock(return_value=("server", "Server", None))
    monkeypatch.setattr(collectors, "process_metadata", metadata)
    records = collectors.collect_psutil()
    assert records[0].local == "[::1]:80"
    assert records[-1].pid is None
    assert metadata.call_count == 2


def test_metadata_survives_partial_permissions(monkeypatch):
    proc = Mock()
    proc.oneshot.return_value = __import__("contextlib").nullcontext()
    proc.create_time.return_value = 1
    proc.name.return_value = "test"
    proc.cmdline.side_effect = psutil.AccessDenied()
    monkeypatch.setattr(collectors.psutil, "Process", Mock(return_value=proc))
    assert collectors.process_metadata(10) == ("test", "test", ProcessIdentity(10, 1))
    proc.is_running.return_value = False
    assert collectors.process_metadata(10)[2] is None
