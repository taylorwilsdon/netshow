# Architecture

`NetshowApp` owns the theme, command palette, and screen stack. `ConnectionsScreen`
owns a complete immutable snapshot plus filter/sort state. One collection worker runs
at a time; refresh requests coalesce. Suspending the screen invalidates in-flight
results, and resuming triggers a fresh collection. Collection errors retain the last
successful snapshot and show its stale status.

Collectors normalize psutil and NUL-delimited lsof output into `Connection` records.
Each refresh reuses process metadata for repeated PIDs. Docker discovery is bounded
and cached for 30 seconds. A non-root collector may see only part of the system;
netshow states this explicitly. lsof and Docker commands have timeouts.

`ConnectionTable` maps row keys to records. Formatting never becomes the source of
process identity or addresses. Filtering/sorting operate locally; table updates preserve
selection by identity and update only changed cells. TCSS uses Textual theme variables.

`BandwidthSampler` owns a separate counter baseline and 60-sample history. A single
worker samples every half-second while the connection screen is active. Rendering and
resizing never sample counters. RX/TX are host/interface totals, not process throughput.

`ProcessInspector` retains its CPU baseline and reports unavailable fields individually.
Termination uses PID plus creation time, revalidated before every signal. The confirmation
screen submits at most one request at a time. A timeout offers a new explicit force-kill
confirmation with Cancel focused. Process trees and privilege escalation are unsupported.

Tests use deterministic collection fixtures and Textual Pilot. Only the explicit child
integration tests signal real processes, and those processes are created by the tests.
`scripts/smoke_install.py` verifies metadata, packaged TCSS, and startup from built artifacts.
