import datetime

import pytest

from ceos_alos2 import decoders


@pytest.mark.parametrize(
    ["scene_id", "expected"],
    (
        pytest.param(
            "ALOS2225333200-180726",
            {
                "mission_name": "ALOS2",
                "orbit_accumulation": "22533",
                "scene_frame": "3200",
                "date": datetime.datetime(2018, 7, 26),
            },
            id="valid_id",
        ),
        pytest.param(
            "ALOS2xxxxx3200-180726",
            ValueError("invalid scene id:"),
            id="invalid_id-invalid_orbit_accumulation",
        ),
        pytest.param(
            "ALOS2225333200-a87433",
            ValueError("invalid scene id"),
            id="invalid_id-invalid_date_chars",
        ),
        pytest.param(
            "ALOS2225333200-987433",
            ValueError("invalid scene id"),
            id="invalid_id-invalid_date",
        ),
    ),
)
def test_decode_scene_id(scene_id, expected):
    if isinstance(expected, Exception):
        with pytest.raises(type(expected), match=expected.args[0]):
            decoders.decode_scene_id(scene_id)

        return

    actual = decoders.decode_scene_id(scene_id)

    assert actual == expected


@pytest.mark.parametrize(
    ["product_id", "expected"],
    (
        pytest.param(
            "WWDR1.1__D",
            {
                "observation_mode": "ScanSAR nominal 28MHz mode dual polarization",
                "observation_direction": "right looking",
                "processing_level": "level 1.1",
                "processing_option": "not specified",
                "map_projection": "not specified",
                "orbit_direction": "descending",
            },
            id="valid_id-l11rd",
        ),
        pytest.param(
            "WWDL1.1__A",
            {
                "observation_mode": "ScanSAR nominal 28MHz mode dual polarization",
                "observation_direction": "left looking",
                "processing_level": "level 1.1",
                "processing_option": "not specified",
                "map_projection": "not specified",
                "orbit_direction": "ascending",
            },
            id="valid_id-l11la",
        ),
        pytest.param(
            "WWDR1.5RUA",
            {
                "observation_mode": "ScanSAR nominal 28MHz mode dual polarization",
                "observation_direction": "right looking",
                "processing_level": "level 1.5",
                "processing_option": "geo-reference",
                "map_projection": "UTM",
                "orbit_direction": "ascending",
            },
            id="valid_id-l15rd",
        ),
        pytest.param(
            "WWDR1.6__A",
            ValueError("invalid product id"),
            id="invalid_id-invalid_level",
        ),
        pytest.param(
            "WRDR1.1__A",
            ValueError("invalid product id"),
            id="invalid_id-wrong_observation_mode",
        ),
    ),
)
def test_decode_product_id(product_id, expected):
    if isinstance(expected, Exception):
        with pytest.raises(type(expected), match=expected.args[0]):
            decoders.decode_product_id(product_id)

        return

    actual = decoders.decode_product_id(product_id)

    assert actual == expected


@pytest.mark.parametrize(
    ["scan_info", "expected"],
    (
        pytest.param(
            "B4",
            {"processing_method": "SPECAN method", "scan_number": "4"},
            id="valid_code",
        ),
        pytest.param("Ac", ValueError("invalid scan info"), id="invalid_code"),
        pytest.param(None, {}, id="empty"),
    ),
)
def test_decode_scan_info(scan_info, expected):
    if isinstance(expected, Exception):
        with pytest.raises(type(expected), match=expected.args[0]):
            decoders.decode_scan_info(scan_info)

        return

    actual = decoders.decode_scan_info(scan_info)

    assert actual == expected


@pytest.mark.parametrize(
    ["path", "expected"],
    (
        pytest.param(
            "IMG-HV-ALOS2225333100-180726-WWDR1.1__D-B3",
            {
                "filetype": "IMG",
                "polarization": "HV",
                "mission_name": "ALOS2",
                "orbit_accumulation": "22533",
                "scene_frame": "3100",
                "date": datetime.datetime(2018, 7, 26, 0, 0, 0),
                "observation_mode": "ScanSAR nominal 28MHz mode dual polarization",
                "observation_direction": "right looking",
                "processing_level": "level 1.1",
                "processing_option": "not specified",
                "map_projection": "not specified",
                "orbit_direction": "descending",
                "processing_method": "SPECAN method",
                "scan_number": "3",
            },
        ),
        pytest.param(
            "TRL-ALOS2225333100-180726-WWDR1.1__D",
            {
                "filetype": "TRL",
                "polarization": None,
                "mission_name": "ALOS2",
                "orbit_accumulation": "22533",
                "scene_frame": "3100",
                "date": datetime.datetime(2018, 7, 26, 0, 0, 0),
                "observation_mode": "ScanSAR nominal 28MHz mode dual polarization",
                "observation_direction": "right looking",
                "processing_level": "level 1.1",
                "processing_option": "not specified",
                "map_projection": "not specified",
                "orbit_direction": "descending",
            },
        ),
        pytest.param(
            "LED-ALOS2290760600-191011-WWDR1.5RUA",
            {
                "filetype": "LED",
                "polarization": None,
                "mission_name": "ALOS2",
                "orbit_accumulation": "29076",
                "scene_frame": "0600",
                "date": datetime.datetime(2019, 10, 11, 0, 0, 0),
                "observation_mode": "ScanSAR nominal 28MHz mode dual polarization",
                "observation_direction": "right looking",
                "processing_level": "level 1.5",
                "processing_option": "geo-reference",
                "map_projection": "UTM",
                "orbit_direction": "ascending",
            },
        ),
        pytest.param("summary.txt", ValueError("invalid file name")),
    ),
)
def test_decode_filename(path, expected):
    if isinstance(expected, Exception):
        with pytest.raises(type(expected), match=expected.args[0]):
            decoders.decode_filename(path)

        return

    actual = decoders.decode_filename(path)

    assert actual == expected
