import datetime

import pytest
from construct import EnumIntegerString
from construct.lib.containers import ListContainer

from ceos_alos2 import utils


@pytest.mark.parametrize(
    ["data", "expected"],
    (
        ("aaceajde", ["a", "c", "e", "j", "d"]),
        ("baebdwea", ["b", "a", "e", "d", "w"]),
    ),
)
def test_unique(data, expected):
    actual = utils.unique(data)

    assert actual == expected


@pytest.mark.parametrize(
    ["f", "args", "kwargs", "expected"],
    (
        pytest.param(lambda x, y: x + y, [1, 2], {}, 3, id="args"),
        pytest.param(lambda x, y: x + y, (2,), {"y": 2}, 4, id="args+kwargs"),
        pytest.param(lambda x, y: x + y, (), {"x": 2, "y": 3}, 5, id="kwargs"),
    ),
)
def test_starcall(f, args, kwargs, expected):
    actual = utils.starcall(f, args, **kwargs)

    assert actual == expected


def test_to_dict():
    container = {
        "_io": None,
        "a": {
            "aa": EnumIntegerString.new(1, "value"),
            "ab": 1,
            "ac": "ac",
            "ad": b"ad",
            "ae": 1j,
            "af": datetime.datetime(1999, 1, 1, 0, 0, 0),
        },
        "b": ListContainer(
            [
                {"ba1": 1},
                {"ba2": 1},
            ]
        ),
        "c": (1, 2, 3),
        "d": [1, 2, 3],
    }
    expected = {
        "a": {
            "aa": "value",
            "ab": 1,
            "ac": "ac",
            "ad": b"ad",
            "ae": 1j,
            "af": datetime.datetime(1999, 1, 1, 0, 0, 0),
        },
        "b": [
            {"ba1": 1},
            {"ba2": 1},
        ],
        "c": (1, 2, 3),
        "d": [1, 2, 3],
    }

    actual = utils.to_dict(container)

    assert actual == expected


@pytest.mark.parametrize(
    ["data", "expected"],
    (
        ("100", 100),
        ("100 MB", 100000000),
        ("100M", 100000000),
        ("5kB", 5000),
        ("5.4 kB", 5400),
        ("1kiB", 1024),
        ("1Mi", 2**20),
        ("1e6", 1000000),
        ("1e6 kB", 1000000000),
        ("MB", 1000000),
        (123, 123),
        (".5GB", 500000000),
        ("123 def", ValueError("Could not interpret '.*' as a byte unit")),
        ("abc# GB", ValueError("Could not interpret '.*' as a number")),
    ),
)
def test_parse_bytes(data, expected):
    if isinstance(expected, Exception):
        with pytest.raises(type(expected), match=expected.args[0]):
            utils.parse_bytes(data)

        return

    actual = utils.parse_bytes(data)

    assert actual == expected
