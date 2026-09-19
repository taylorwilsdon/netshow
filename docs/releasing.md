# Releasing netshow

The package version lives only in `pyproject.toml`; the CLI reads installed metadata.
The UI refresh keeps the existing version during development. Assign the next release
version explicitly when preparing the release (a minor release is appropriate).

1. Update the version and release notes. Run `uv lock` to update the local package entry.
2. Run `python release.py`. This checks formatting, lint, typing, tests, and builds artifacts.
3. Smoke-test **both** artifacts, substituting the chosen version:

   ```sh
   uv run --no-project --isolated --with ./dist/netshow-VERSION-py3-none-any.whl python scripts/smoke_install.py
   uv run --no-project --isolated --with ./dist/netshow-VERSION.tar.gz python scripts/smoke_install.py
   ```

4. Exercise the app on Linux and macOS, unprivileged and privileged: collect TCP states,
   open/close details, filter/sort, change interfaces, resize, and terminate a disposable
   process you started for this check. Confirm force kill separately using a disposable
   process that ignores SIGTERM. Check ASCII/monochrome and ANSI themes in real terminals.
5. Review and commit the release files, then create an annotated `vVERSION` tag and push
   normally. Never rewrite remote history as part of a release.
6. Publish only the two reviewed versioned artifacts with `uv publish <wheel> <sdist>`.
   Prefer trusted publishing or a token supplied through the environment; never store
   credentials in the repository. Create the GitHub release from the matching tag.

Old versions remain available to Python 3.9/3.10 users. The new release requires 3.11+.
There is no configuration migration, background service, or telemetry to deploy.
