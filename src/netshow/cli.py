"""CLI entry point for NetShow."""

import sys

from .app import NetshowApp


def main() -> None:
    """Main CLI entry point."""
    try:
        NetshowApp().run()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
