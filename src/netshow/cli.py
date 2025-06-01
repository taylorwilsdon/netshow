"""CLI entry point for NetShow."""

import sys

from .app import NetTopApp


def main():
    """Main CLI entry point."""
    try:
        NetTopApp().run()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
