import pytest

from ceos_alos2 import transformers


@pytest.mark.parametrize(
    ["s", "expected"],
    (
        ("1990012012563297", "1990-01-20T12:56:32.970000"),
        ("2001112923595915", "2001-11-29T23:59:59.150000"),
    ),
)
def test_parse_datetime(s, expected):
    actual = transformers.normalize_datetime(s)

    assert actual == expected
