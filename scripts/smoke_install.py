"""Run against an installed wheel or sdist, without development dependencies."""

import asyncio
from importlib.metadata import version
from importlib.resources import files

from netshow import __version__
from netshow.app import NetshowApp
from netshow.connection_table import ConnectionTable
from netshow.models import CollectionResult


async def main() -> None:
    assert __version__ == version("netshow")
    assert files("netshow").joinpath("netshow.tcss").is_file()
    app = NetshowApp(collector=CollectionResult)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.connections.query_one(ConnectionTable).row_count == 0
    print(f"Installed netshow {__version__}: metadata, stylesheet, and UI OK")


if __name__ == "__main__":
    asyncio.run(main())
