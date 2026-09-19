import os
import subprocess
import sys
from contextlib import nullcontext
from unittest.mock import Mock

import psutil
import pytest

from netshow import processes
from netshow.models import ProcessIdentity


@pytest.fixture
def proc(monkeypatch):
    process = Mock()
    process.create_time.return_value = 100
    process.is_running.return_value = True
    process.oneshot.return_value = nullcontext()
    monkeypatch.setattr(processes.psutil, "Process", Mock(return_value=process))
    return process


def test_graceful_then_separate_force(proc):
    identity = ProcessIdentity(123456, 100)
    proc.wait.side_effect = psutil.TimeoutExpired(3)
    assert processes.signal_process(identity).state == "alive"
    proc.terminate.assert_called_once()
    proc.kill.assert_not_called()
    proc.wait.side_effect = None
    assert processes.signal_process(identity, force=True).state == "exited"
    proc.kill.assert_called_once()


def test_pid_reuse_never_signals(proc):
    proc.create_time.return_value = 101
    assert processes.signal_process(ProcessIdentity(123456, 100)).state == "changed"
    proc.terminate.assert_not_called()
    proc.kill.assert_not_called()


def test_permission_denied_and_already_exited(proc):
    identity = ProcessIdentity(123456, 100)
    proc.terminate.side_effect = psutil.AccessDenied()
    assert processes.signal_process(identity).state == "denied"
    proc.terminate.side_effect = psutil.NoSuchProcess(123456)
    assert processes.signal_process(identity).state == "exited"


@pytest.mark.parametrize("pid", [0, 1, os.getpid()])
def test_protected_processes(proc, pid):
    assert processes.signal_process(ProcessIdentity(pid, 100)).state == "protected"
    proc.terminate.assert_not_called()
    assert processes.control_unavailable(None)


def test_partial_details_and_cpu_baseline(proc):
    proc.name.return_value = "service"
    proc.username.return_value = "user"
    proc.exe.side_effect = psutil.AccessDenied()
    proc.cwd.return_value = "/tmp"
    proc.cmdline.return_value = ["service", "[literal]"]
    proc.status.return_value = "running"
    proc.cpu_percent.return_value = 12.5
    proc.memory_percent.return_value = 1.5
    inspector = processes.ProcessInspector(ProcessIdentity(123456, 100))
    fields = dict(inspector.sample().fields)
    assert fields["Name"] == "service"
    assert fields["Executable"] == "Permission denied"
    assert fields["CPU"] == "Sampling…"
    fields = dict(inspector.sample().fields)
    assert fields["CPU"] == "12.5%"
    proc.exe.assert_called_once()


def test_process_exit_during_inspection(proc):
    proc.create_time.side_effect = psutil.NoSuchProcess(123456)
    assert (
        processes.ProcessInspector(ProcessIdentity(123456, 100)).sample().error == "Process exited."
    )


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signals")
def test_terminate_only_test_owned_child():
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        identity = ProcessIdentity(child.pid, psutil.Process(child.pid).create_time())
        assert processes.signal_process(identity).state == "exited"
    finally:
        if child.poll() is None:
            child.kill()
        child.wait()
