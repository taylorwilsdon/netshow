from types import SimpleNamespace
from unittest.mock import Mock

from netshow import bandwidth
from netshow.bandwidth import BandwidthSampler
from netshow.presentation import format_bytes


def test_rates_use_monotonic_elapsed_time():
    sampler = BandwidthSampler()
    assert sampler.observe("all", 10, 1000, 2000).received == 0
    sample = sampler.observe("all", 12, 3000, 3000)
    assert sample.received == 1000
    assert sample.sent == 500
    assert list(sampler.history) == [1500]


def test_switch_and_counter_reset_clear_history():
    sampler = BandwidthSampler()
    sampler.observe("all", 1, 0, 0)
    sampler.observe("all", 2, 100, 100)
    assert sampler.observe("en0", 3, 10000, 10000).received == 0
    assert not sampler.history
    sampler.observe("en0", 4, 20000, 20000)
    assert sampler.observe("en0", 5, 1, 1).sent == 0
    assert not sampler.history
    assert sampler.observe("en0", 5, 100, 100).sent == 0


def test_interface_removal_and_unavailable_counters(monkeypatch):
    sampler = BandwidthSampler()
    sampler.observe("gone", 1, 100, 100)
    monkeypatch.setattr(
        bandwidth.psutil,
        "net_io_counters",
        Mock(return_value={"lo": SimpleNamespace(bytes_recv=500, bytes_sent=500)}),
    )
    sample = sampler.sample("gone")
    assert sample.interface == "all"
    assert sample.received == 0
    assert sampler.interfaces == ["all", "lo"]
    monkeypatch.setattr(bandwidth.psutil, "net_io_counters", Mock(return_value={}))
    assert not sampler.sample("all").available
    monkeypatch.setattr(bandwidth.psutil, "net_io_counters", Mock(side_effect=OSError()))
    assert not sampler.sample("all").available


def test_byte_format_keeps_fraction():
    assert format_bytes(1536) == "1.5 KiB"
