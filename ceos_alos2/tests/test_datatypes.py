import datetime

import numpy as np
import pytest
from construct import Bytes, Int8ub, Int32ub, Int64ub, Struct

from ceos_alos2 import datatypes


@pytest.mark.parametrize(
    ["data", "n_bytes", "expected"],
    (
        pytest.param(b"15", 2, 15, id="2bytes-no_padding"),
        pytest.param(b"3989", 4, 3989, id="4bytes-no_padding"),
        pytest.param(b"  16", 4, 16, id="4bytes-padding"),
        pytest.param(b"    ", 4, -1, id="4bytes-all_padding"),
    ),
)
def test_ascii_integer(data, n_bytes, expected):
    parser = datatypes.AsciiInteger(n_bytes)

    actual = parser.parse(data)
    assert actual == expected

    with pytest.raises(NotImplementedError):
        parser.build(expected)


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

    with pytest.raises(NotImplementedError):
        parser.build(expected)


@pytest.mark.parametrize(
    ["data", "n_bytes", "expected"],
    (
        pytest.param(b"1.558.42", 8, 1.55 + 8.42j, id="8bytes-no_padding"),
        pytest.param(b"        ", 8, float("nan") + 1j * float("nan"), id="8bytes-all_padding"),
        pytest.param(b"162.3659487.8321", 16, 162.3659 + 487.8321j, id="16bytes-no_padding"),
        pytest.param(b" 62.3659 87.8321", 16, 62.3659 + 87.8321j, id="16bytes-padding"),
    ),
)
def test_ascii_complex(data, n_bytes, expected):
    parser = datatypes.AsciiComplex(n_bytes)

    actual = parser.parse(data)
    np.testing.assert_equal(actual, expected)

    with pytest.raises(NotImplementedError):
        parser.build(expected)


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

    with pytest.raises(NotImplementedError):
        parser.build(expected)


@pytest.mark.parametrize(
    ["data", "factor", "expected"],
    (
        pytest.param(b"\x32", 1e-2, 0.5, id="negative_factor"),
        pytest.param(b"\x32", 1e3, 50000, id="positive_factor"),
    ),
)
def test_factor(data, factor, expected):
    base = Int8ub
    parser = datatypes.Factor(base, factor=factor)

    actual = parser.parse(data)

    assert actual == expected

    with pytest.raises(NotImplementedError):
        parser.build(expected)


@pytest.mark.parametrize(
    ["data", "expected"],
    (
        pytest.param(
            b"\x00\x00\x07\xc6\x00\x00\x01\x0e\x03\x19\xf2f",
            datetime.datetime(1990, 9, 27, 14, 27, 12, 102000),
        ),
        pytest.param(
            b"\x00\x00\x08\x0b\x00\x00\x00\x01\x00\x00\x00\x00",
            datetime.datetime(2059, 1, 1),
        ),
    ),
)
def test_datetime_ydms(data, expected):
    base = Struct(
        "year" / Int32ub,
        "day_of_year" / Int32ub,
        "milliseconds" / Int32ub,
    )

    parser = datatypes.DatetimeYdms(base)

    actual = parser.parse(data)

    assert actual == expected

    with pytest.raises(NotImplementedError):
        parser.build(expected)


@pytest.mark.parametrize(
    ["data", "expected"],
    (
        pytest.param(
            b"\x00\x00\x00\x00\x00\x00\x00\x00",
            datetime.datetime(2019, 1, 1),
            id="offset_zero",
        ),
        pytest.param(
            b"\x00\x00\x00\tx\x0f\xb1@",
            datetime.datetime(2019, 1, 1, 11, 17, 49),
            id="full_seconds",
        ),
    ),
)
def test_datetime_ydus(data, expected):
    reference_date = datetime.datetime(2019, 1, 1, 21, 37, 52, 107000)

    parser = datatypes.DatetimeYdus(Int64ub, reference_date)
    actual = parser.parse(data)

    assert actual == expected

    with pytest.raises(NotImplementedError):
        parser.build(expected)


@pytest.mark.parametrize(
    ["metadata"],
    (
        pytest.param({"units": "m"}),
        pytest.param({"scale": 10, "units": "us"}),
    ),
)
def test_metadata(metadata):
    data = b"\x32"
    base = Int8ub

    expected = (50, metadata)

    parser = datatypes.Metadata(base, **metadata)
    actual = parser.parse(data)

    assert actual == expected

    with pytest.raises(NotImplementedError):
        parser.build(expected)


@pytest.mark.parametrize(
    ["data", "expected"],
    (
        pytest.param(b"\x01", b"\x01", id="no_padding"),
        pytest.param(b"\x00\x01", b"\x01", id="left_padding-1"),
        pytest.param(b"\x00\x00\x01", b"\x01", id="left_padding-2"),
        pytest.param(b"\x01\x00", b"\x01", id="right_padding-1"),
        pytest.param(b"\x01\x00\x00", b"\x01", id="right_padding-2"),
        pytest.param(b"\x00\x01\x00", b"\x01", id="both_padding-1"),
        pytest.param(b"\x00\x00\x01\x00\x00", b"\x01", id="both_padding-1"),
        pytest.param(b"\x01\x00\x01", b"\x01\x00\x01", id="mid"),
    ),
)
def test_strip_null_bytes(data, expected):
    base = Bytes(len(data))
    parser = datatypes.StripNullBytes(base)

    actual = parser.parse(data)
    assert actual == expected

    with pytest.raises(NotImplementedError):
        parser.build(expected)
