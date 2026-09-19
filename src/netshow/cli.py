"""Command-line entry point."""

import argparse
import math
import os

from . import __version__
from .app import NetshowApp


def positive_interval(value: str) -> float:
    try:
        interval = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("interval must be a positive number") from error
    if not math.isfinite(interval) or interval <= 0:
        raise argparse.ArgumentTypeError("interval must be finite and greater than zero")
    return interval


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactive TCP connection and process monitor")
    parser.add_argument("--interval", type=positive_interval, default=3.0, metavar="SECONDS")
    parser.add_argument("--no-colors", action="store_true", help="use monochrome rendering")
    parser.add_argument("--version", action="version", version=f"netshow {__version__}")
    args = parser.parse_args()
    try:
        NetshowApp(
            interval=args.interval, no_colors=args.no_colors or bool(os.getenv("NO_COLOR"))
        ).run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
