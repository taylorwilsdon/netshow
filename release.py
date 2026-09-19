"""Check and build local release artifacts. Publishing is documented in docs/releasing.md."""

import subprocess
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    commands = [
        ["uv", "sync", "--locked"],
        ["uv", "run", "--locked", "ruff", "format", "--check", "."],
        ["uv", "run", "--locked", "ruff", "check", "."],
        ["uv", "run", "--locked", "mypy", "src"],
        ["uv", "run", "--locked", "pytest", "-q"],
        ["uv", "build"],
    ]
    for command in commands:
        subprocess.run(command, cwd=root, check=True)
    print("Local artifacts built. Review docs/releasing.md before tagging or publishing.")


if __name__ == "__main__":
    main()
