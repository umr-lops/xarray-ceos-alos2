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
