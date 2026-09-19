from unittest.mock import Mock

import pytest

from netshow import __version__, cli


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "-inf", "bad"])
def test_invalid_interval(value):
    with pytest.raises(cli.argparse.ArgumentTypeError):
        cli.positive_interval(value)


def test_options_and_no_color(monkeypatch):
    app = Mock()
    monkeypatch.setattr(cli, "NetshowApp", app)
    monkeypatch.setattr("sys.argv", ["netshow", "--interval", "1.5"])
    monkeypatch.setenv("NO_COLOR", "1")
    cli.main()
    app.assert_called_once_with(interval=1.5, no_colors=True)
    app.return_value.run.assert_called_once()


def test_version(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["netshow", "--version"])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 0
    assert __version__ in capsys.readouterr().out
