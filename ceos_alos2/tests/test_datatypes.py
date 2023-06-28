import numpy as np
import pytest

from ceos_alos2 import datatypes


@pytest.mark.parametrize(
    ["data", "n_bytes", "expected"],
    (
        pytest.param(b"15", 2, 15, id="2bytes-no_padding"),
        pytest.param(b"3989", 4, 3989, id="4bytes-no_padding"),
        pytest.param(b"16  ", 4, 16, id="4bytes-padding"),
        pytest.param(b"    ", 4, -1, id="4bytes-all_padding"),
    ),
)
def test_ascii_integer(data, n_bytes, expected):
    parser = datatypes.AsciiInteger(n_bytes)

    actual = parser.parse(data)
    assert actual == expected


@pytest.mark.parametrize(
    ["data", "n_bytes", "expected"],
    (
        pytest.param(b"1558.423", 8, 1558.423, id="8bytes-no_padding"),
        pytest.param(b" 165.820", 8, 165.820, id="8bytes-padding"),
        pytest.param(b"        ", 8, float("nan"), id="8bytes-all_padding"),
        pytest.param(b"162436598487.832", 16, 162436598487.832, id="16bytes-no_padding"),
        pytest.param(b"     6598487.832", 16, 6598487.832, id="16bytes-padding"),
    ),
)
def test_ascii_float(data, n_bytes, expected):
    parser = datatypes.AsciiFloat(n_bytes)

    actual = parser.parse(data)
    np.testing.assert_equal(actual, expected)


@pytest.mark.parametrize(
    ["data", "n_bytes", "expected"],
    (
        pytest.param(b"ALOS", 4, "ALOS", id="4bytes-no_padding"),
        pytest.param(b"abc ", 4, "abc", id="4bytes-padding"),
    ),
)
def test_padded_string(data, n_bytes, expected):
    parser = datatypes.PaddedString(n_bytes)

    actual = parser.parse(data)
    assert actual == expected
