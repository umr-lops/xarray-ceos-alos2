import pytest

from ceos_alos2 import summary

try:
    ExceptionGroup
except NameError:  # pragma: no cover
    from exceptiongroup import ExceptionGroup


def compare_exceptions(e1, e2):
    return type(e1) is type(e2) and e1.args == e2.args


@pytest.mark.parametrize(
    ["line", "expected"],
    (
        pytest.param(
            'Scs_SceneShift="0"',
            {"section": "Scs", "keyword": "SceneShift", "value": "0"},
            id="valid_line1",
        ),
        pytest.param(
            'Pds_ProductID="WWDR1.1__D"',
            {"section": "Pds", "keyword": "ProductID", "value": "WWDR1.1__D"},
            id="valid_line2",
        ),
        pytest.param('Scs_SceneShift"0"', ValueError("invalid line"), id="invalid_line1"),
        pytest.param(
            'PdsProductID="WWDR1.1__D"',
            ValueError("invalid line"),
            id="invalid_line2",
        ),
    ),
)
def test_parse_line(line, expected):
    if isinstance(expected, Exception):
        with pytest.raises(type(expected), match=expected.args[0]):
            summary.parse_line(line)
        return

    actual = summary.parse_line(line)

    assert actual == expected


@pytest.mark.parametrize(
    ["content", "expected"],
    (
        pytest.param(
            'Scs_SceneShift="0"\nPds_ProductID="WWDR1.1__D"',
            {"scs": {"SceneShift": "0"}, "pds": {"ProductID": "WWDR1.1__D"}},
            id="valid_lines",
        ),
        pytest.param(
            'Scs_SceneShift"0"\nPdsProductID="WWDR1.1__D"',
            ExceptionGroup(
                "failed to parse the summary",
                [
                    ValueError("line 00: invalid line"),
                    ValueError("line 01: invalid line"),
                ],
            ),
            id="invalid_lines",
        ),
    ),
)
def test_parse_summary(content, expected):
    if isinstance(expected, Exception):
        with pytest.raises(type(expected)) as e:
            summary.parse_summary(content)

        assert e.value.message == expected.message
        assert all(
            compare_exceptions(e1, e2) for e1, e2 in zip(e.value.exceptions, expected.exceptions)
        )
        return
    actual = summary.parse_summary(content)
    assert actual == expected
