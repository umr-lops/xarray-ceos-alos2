import pytest

from ceos_alos2 import summary
from ceos_alos2.hierarchy import Group
from ceos_alos2.testing import assert_identical

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


@pytest.mark.parametrize(
    ["mapping", "expected"],
    (
        pytest.param(
            {"1": "vd", "2": "l", "3": "im1", "4": "im2", "5": "tr"},
            {
                "volume_directory": "vd",
                "sar_leader": "l",
                "sar_imagery": ["im1", "im2"],
                "sar_trailer": "tr",
            },
            id="normal",
        ),
        pytest.param(
            {"1": "vd", "2": "l", "3": "im1", "4": "im2", "5": "im3", "6": "im4", "7": "tr"},
            {
                "volume_directory": "vd",
                "sar_leader": "l",
                "sar_imagery": ["im1", "im2", "im3", "im4"],
                "sar_trailer": "tr",
            },
            id="long",
        ),
        pytest.param({"1": "vd", "2": "l"}, ValueError(""), id="short"),
    ),
)
def test_categorize_filenames(mapping, expected):
    if isinstance(expected, Exception):
        with pytest.raises(type(expected), match=expected.args[0]):
            summary.categorize_filenames(mapping)

        return

    actual = summary.categorize_filenames(mapping)
    assert actual == expected


@pytest.mark.parametrize(
    ["date", "expected"],
    (
        pytest.param("20190109", "2019-01-09"),
        pytest.param("19971231", "1997-12-31"),
    ),
)
def test_reformat_date(date, expected):
    actual = summary.reformat_date(date)

    assert actual == expected


@pytest.mark.parametrize(
    ["date", "expected"],
    (
        pytest.param("20190109 02:37:01.764", "2019-01-09T02:37:01.764"),
        pytest.param("19971231 12:29:46.182", "1997-12-31T12:29:46.182"),
    ),
)
def test_to_isoformat(date, expected):
    actual = summary.to_isoformat(date)

    assert actual == expected


@pytest.mark.parametrize(
    ["funcs", "default", "expected"],
    (
        pytest.param(
            {"a": int, "b": str, "c": float}, summary.passthrough, {"a": 1, "b": "6.4", "c": 4.0}
        ),
        pytest.param({"a": int, "c": float}, summary.passthrough, {"a": 1, "b": 6.4, "c": 4.0}),
        pytest.param({"b": str}, lambda x: x * 2, {"a": "11", "b": "6.4", "c": 8}),
    ),
)
def test_apply_to_items(funcs, default, expected):
    mapping = {"a": "1", "b": 6.4, "c": 4}

    actual = summary.apply_to_items(funcs, mapping, default=default)

    assert actual == expected


@pytest.mark.parametrize(
    ["section", "expected"],
    (
        pytest.param(
            {"SceneId": "abc", "SiteDateTime": "def"},
            Group(path=None, url=None, data={}, attrs={"SceneId": "abc", "SiteDateTime": "def"}),
        ),
        pytest.param(
            {"SceneId": "ab", "SiteDateTime": "cd"},
            Group(path=None, url=None, data={}, attrs={"SceneId": "ab", "SiteDateTime": "cd"}),
        ),
    ),
)
def test_transform_ordering_info(section, expected):
    actual = summary.transform_ordering_info(section)

    assert_identical(actual, expected)


@pytest.mark.parametrize(
    ["section", "expected"],
    (
        pytest.param(
            {"SceneID": "ALOS2290760600-191011", "SceneShift": "0"},
            Group(
                path=None,
                url=None,
                data={},
                attrs={
                    "mission_name": "ALOS2",
                    "orbit_accumulation": 29076,
                    "scene_frame": 600,
                    "date": "2019-10-11",
                    "SceneShift": 0,
                },
            ),
            id="scene1",
        ),
        pytest.param(
            {"SceneID": "ALOS2225333200-180726", "SceneShift": "1"},
            Group(
                path=None,
                url=None,
                data={},
                attrs={
                    "mission_name": "ALOS2",
                    "orbit_accumulation": 22533,
                    "scene_frame": 3200,
                    "date": "2018-07-26",
                    "SceneShift": 1,
                },
            ),
            id="scene2",
        ),
    ),
)
def test_transform_scene_spec(section, expected):
    actual = summary.transform_scene_spec(section)

    assert_identical(actual, expected)


@pytest.mark.parametrize(
    ["section", "expected"],
    (
        pytest.param(
            {"ProductID": "WWDR1.1__D"},
            Group(
                path=None,
                url=None,
                data={},
                attrs={
                    "observation_mode": "ScanSAR nominal 28MHz mode dual polarization",
                    "observation_direction": "right looking",
                    "processing_level": "level 1.1",
                    "processing_option": "not specified",
                    "map_projection": "not specified",
                    "orbit_direction": "descending",
                },
            ),
            id="product_id1",
        ),
        pytest.param(
            {"ProductID": "WWDR1.5RUA"},
            Group(
                path=None,
                url=None,
                data={},
                attrs={
                    "observation_mode": "ScanSAR nominal 28MHz mode dual polarization",
                    "observation_direction": "right looking",
                    "processing_level": "level 1.5",
                    "processing_option": "geo-reference",
                    "map_projection": "UTM",
                    "orbit_direction": "ascending",
                },
            ),
            id="product_id2",
        ),
        pytest.param(
            {"PixelSpacing": "25.000000"},
            Group(path=None, url=None, data={}, attrs={"PixelSpacing": 25.0}),
            id="floats",
        ),
        pytest.param(
            {
                "ResamplingMethod": "NN",
                "UTM_ZoneNo": "53",
                "OrbitDataPrecision": "Precision",
                "AttitudeDataPrecision": "Onboard",
                "MapDirection": "MapNorth",
            },
            Group(
                path=None,
                url=None,
                data={},
                attrs={
                    "ResamplingMethod": "nearest-neighbor",
                    "UTM_ZoneNo": 53,
                    "OrbitDataPrecision": "Precision",
                    "AttitudeDataPrecision": "Onboard",
                    "MapDirection": "MapNorth",
                },
            ),
            id="other_metadata",
        ),
    ),
)
def test_transform_product_spec(section, expected):
    actual = summary.transform_product_spec(section)

    assert_identical(actual, expected)


@pytest.mark.parametrize(
    ["section", "expected"],
    (
        pytest.param(
            {
                "SceneCenterDateTime": "20191011 14:43:15.525",
                "SceneStartDateTime": "20191011 14:42:49.525",
                "SceneEndDateTime": "20191011 14:43:41.524",
            },
            Group(
                path=None,
                url=None,
                data={},
                attrs={
                    "SceneCenterDateTime": "2019-10-11T14:43:15.525",
                    "SceneStartDateTime": "2019-10-11T14:42:49.525",
                    "SceneEndDateTime": "2019-10-11T14:43:41.524",
                },
            ),
            id="datetime",
        ),
        pytest.param(
            {
                "ImageSceneCenterLatitude": "30.385",
                "ImageSceneCenterLongitude": "137.504",
                "OffNadirAngle": "21.3",
            },
            Group(
                path=None,
                url=None,
                data={},
                attrs={
                    "ImageSceneCenterLatitude": 30.385,
                    "ImageSceneCenterLongitude": 137.504,
                    "OffNadirAngle": 21.3,
                },
            ),
            id="floats",
        ),
    ),
)
def test_transform_image_info(section, expected):
    actual = summary.transform_image_info(section)

    assert_identical(actual, expected)


@pytest.mark.parametrize(
    ["section", "expected"],
    (
        pytest.param(
            {"TimeCheck": "GOOD", "AttitudeCheck": "POOR"},
            Group(
                path=None, url=None, data={}, attrs={"TimeCheck": "GOOD", "AttitudeCheck": "POOR"}
            ),
            id="available",
        ),
        pytest.param(
            {"AbsoluteNavigationTime": "", "PRF_Check": ""},
            Group(
                path=None,
                url=None,
                data={},
                attrs={"AbsoluteNavigationTime": "N/A", "PRF_Check": "N/A"},
            ),
            id="missing",
        ),
    ),
)
def test_transform_autocheck(section, expected):
    actual = summary.transform_autocheck(section)

    assert_identical(actual, expected)


@pytest.mark.parametrize(
    ["section", "expected"],
    (
        pytest.param(
            {"PracticeResultCode": "GOOD"},
            Group(path=None, url=None, data={}, attrs={"PracticeResultCode": "GOOD"}),
            id="good",
        ),
        pytest.param(
            {"PracticeResultCode": "FAIR"},
            Group(path=None, url=None, data={}, attrs={"PracticeResultCode": "FAIR"}),
            id="fair",
        ),
    ),
)
def test_transform_result_info(section, expected):
    actual = summary.transform_result_info(section)

    assert_identical(actual, expected)


@pytest.mark.parametrize(
    ["section", "expected"],
    (
        pytest.param(
            {"ObservationDate": "20191011"},
            Group(path=None, url=None, data={}, attrs={"ObservationDate": "2019-10-11"}),
            id="datetime1",
        ),
        pytest.param(
            {"ObservationDate": "20180726"},
            Group(path=None, url=None, data={}, attrs={"ObservationDate": "2018-07-26"}),
            id="datetime2",
        ),
        pytest.param(
            {"ProcessFacility": "SCMO"},
            Group(
                path=None,
                url=None,
                data={},
                attrs={"ProcessFacility": "spacecraft control mission operation system"},
            ),
            id="facility1",
        ),
        pytest.param(
            {"ProcessFacility": "EICS"},
            Group(
                path=None,
                url=None,
                data={},
                attrs={"ProcessFacility": "earth intelligence collection and sharing system"},
            ),
            id="facility2",
        ),
        pytest.param(
            {"Satellite": "ALOS2", "Sensor": "SAR", "ProcessLevel": "1.1"},
            Group(
                path=None,
                url=None,
                data={},
                attrs={"Satellite": "ALOS2", "Sensor": "SAR", "ProcessLevel": "1.1"},
            ),
            id="other_metadata",
        ),
    ),
)
def test_transform_label_info(section, expected):
    actual = summary.transform_label_info(section)

    assert_identical(actual, expected)
