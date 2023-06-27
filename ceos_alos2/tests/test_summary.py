import pytest

from ceos_alos2 import summary


@pytest.mark.parametrize(
    ["lines", "expected"],
    (
        pytest.param(
            ['Scs_SceneShift="0"', 'Pds_ProductID="WWDR1.1__D"'],
            [
                {"section": "Scs", "keyword": "SceneShift", "value": "0"},
                {"section": "Pds", "keyword": "ProductID", "value": "WWDR1.1__D"},
            ],
            id="valid_lines",
        ),
        pytest.param(
            ['Scs_SceneShift"0"', 'PdsProductID="WWDR1.1__D"'],
            [ValueError("line 00: invalid line"), ValueError("line 01: invalid line")],
            id="invalid_lines",
        ),
    ),
)
def test_parse_lines(lines, expected):
    actual = list(summary.parse_lines(lines))

    assert actual == expected


@pytest.mark.parametrize(
    ["entries", "expected"],
    (
        pytest.param([{"a": 1}, {"b": 2}], ([{"a": 1}, {"b": 2}], []), id="no_errors"),
        pytest.param(
            [ValueError("invalid line"), ValueError("invalid line")],
            ([], [ValueError("invalid line"), ValueError("invalid line")]),
            id="all_errors",
        ),
        pytest.param(
            [{"a": 1}, ValueError("invalid line")],
            ([{"a": 1}], [ValueError("invalid line")]),
            id="mixed",
        ),
    ),
)
def test_extract_errors(entries, expected):
    actual_entries, actual_errors = summary.extract_errors(entries)

    assert len(entries) == len(actual_entries) + len(actual_errors)
    assert all(
        entry in entries and not isinstance(entry, Exception)
        for entry in actual_entries
    )
    assert all(
        entry in entries and isinstance(entry, Exception) for entry in actual_errors
    )
