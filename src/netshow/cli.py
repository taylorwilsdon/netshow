"""CLI entry point for NetShow."""

import os
import sys

from .app import NetshowApp


def main() -> None:
    """Main CLI entry point."""
    # Ensure truecolor support for Solarized theme
    if "COLORTERM" not in os.environ:
        os.environ["COLORTERM"] = "truecolor"

    try:
        NetshowApp().run()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
