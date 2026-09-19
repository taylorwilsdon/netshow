from netshow.models import Connection
from netshow.presentation import address, literal, select_connections


def test_filter_sort_and_default_order():
    first = Connection(10, "b", "beta", "[::1]:80", "", "LISTEN")
    second = Connection(20, "a", "alpha", "127.0.0.1:80", "", "ESTABLISHED")
    assert select_connections([second, first], "", "default")[0] == [first, second]
    assert select_connections([first, second], "", "process")[0] == [second, first]
    assert select_connections([first, second], "20", "default")[0] == [second]
    assert select_connections([first, second], "[", "default") == ([first], True)
    assert select_connections([first, second], "ALPHA|LISTEN", "default")[0] == [first, second]


def test_literal_and_full_address():
    assert literal("[bold]hi[/bold]\x1b\x00\n") == "[bold]hi[/bold]   "
    assert address("[::1]:80", False) == "[…]:80"
    assert address("[::1]:80", True) == "[::1]:80"
