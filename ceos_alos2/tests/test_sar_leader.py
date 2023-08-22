import fsspec
import numpy as np
import pytest

from ceos_alos2.hierarchy import Group, Variable
from ceos_alos2.sar_leader import (
    attitude,
    data_quality_summary,
    dataset_summary,
    facility_related_data,
    io,
    map_projection,
    metadata,
    platform_position,
    radiometric_data,
)
from ceos_alos2.testing import assert_identical


@pytest.mark.parametrize(
    ["mapping", "expected"],
    (
        pytest.param(
            {
                "preamble": "",
                "spare1": "",
                "dataset_summary_records_sequence_number": "",
                "sar_channel_id": "",
                "number_of_scene_reference": "",
                "average_terrain_height_above_ellipsoid_at_scene_center": "",
                "processing_scene_length": 1,
                "processing_scene_width": 2,
                "range_pulse_phase_coefficients": {},
                "processing_code_of_processing_facility": "",
                "processing_algorithm_id": "",
                "radiometric_bias": 0,
                "radiometric_gain": "",
                "time_direction_indicator_along_pixel_direction": "",
                "spare72": "",
                "parameter_table_number_of_automatically_setting": 0,
                "image_annotation_segment": {},
                "spare_width": 0,
            },
            Group(path=None, url=None, data={}, attrs={"spare_width": 0}),
            id="ignored",
        ),
        pytest.param(
            {"scene_center_time": "2020101117213774"},
            Group(
                path=None,
                url=None,
                data={},
                attrs={"scene_center_time": "2020-10-11T17:21:37.740000"},
            ),
            id="transformers",
        ),
        pytest.param(
            {
                "scene_id": "abc",
                "geodetic_latitude": (61.6, {"units": "deg"}),
                "range_pulse_amplitude_coefficients": {"a0": 0, "a1": 1},
                "incidence_angle": (
                    {"a0": (0, {"units": "rad"}), "a1": (0.5, {"units": "rad/km"})},
                    {"formula": "def"},
                ),
            },
            Group(
                path=None,
                url=None,
                data={
                    "geodetic_latitude": Variable((), 61.6, {"units": "deg"}),
                    "range_pulse_amplitude_coefficients": Group(
                        path=None, url=None, data={}, attrs={"a0": 0, "a1": 1}
                    ),
                    "incidence_angle": Group(
                        path=None,
                        url=None,
                        data={
                            "a0": Variable((), 0, {"units": "rad"}),
                            "a1": Variable((), 0.5, {"units": "rad/km"}),
                        },
                        attrs={"formula": "def"},
                    ),
                },
                attrs={"scene_id": "abc"},
            ),
            id="groups",
        ),
    ),
)
def test_transform_dataset_summary(mapping, expected):
    actual = dataset_summary.transform_dataset_summary(mapping)

    assert_identical(actual, expected)


class TestMapProjection:
    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param({"a": 1}, {"a": 1}, id="no_projection"),
            pytest.param(
                {
                    "map_projection_designator": "UTM-PROJECTION",
                    "utm_projection": {"type": "UNIVERSAL TRANSVERSE MERCATOR"},
                    "ups_projection": {"type": ""},
                    "national_system_projection": {"projection_descriptor": ""},
                },
                {"projection": {"type": "UNIVERSAL TRANSVERSE MERCATOR"}},
                id="utm",
            ),
            pytest.param(
                {
                    "map_projection_designator": "UPS-PROJECTION",
                    "utm_projection": {"zone": ""},
                    "ups_projection": {"type": "UNIVERSAL POLAR STEREOGRAPHIC"},
                    "national_system_projection": {"projection_descriptor": ""},
                },
                {"projection": {"type": "UNIVERSAL POLAR STEREOGRAPHIC"}},
                id="ups",
            ),
            pytest.param(
                {
                    "map_projection_designator": "LCC-PROJECTION",
                    "utm_projection": {"zone": ""},
                    "ups_projection": {"type": ""},
                    "national_system_projection": {
                        "projection_descriptor": "LAMBERT-CONFORMAL CONIC"
                    },
                },
                {"projection": {"projection_descriptor": "LAMBERT-CONFORMAL CONIC"}},
                id="lcc",
            ),
            pytest.param(
                {
                    "map_projection_designator": "MER-PROJECTION",
                    "utm_projection": {"zone": ""},
                    "ups_projection": {"type": ""},
                    "national_system_projection": {"projection_descriptor": "MERCATOR"},
                },
                {"projection": {"projection_descriptor": "MERCATOR"}},
                id="mer",
            ),
        ),
    )
    def test_filter_map_projection(self, mapping, expected):
        actual = map_projection.filter_map_projection(mapping)

        assert actual == expected

    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param(
                {"map_projection_type": "GEOREFERENCE"},
                {"map_projection_type": "GEOREFERENCE"},
                id="no_rename",
            ),
            pytest.param(
                {"number_of_pixels_per_line": 2, "number_of_lines": 4},
                {"n_columns": 2, "n_rows": 4},
                id="renames",
            ),
        ),
    )
    def test_transform_general_info(self, mapping, expected):
        actual = map_projection.transform_general_info(mapping)

        assert actual == expected

    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param({"datum_shift_parameters": {"a": 1, "b": 2}}, {}, id="ignored1"),
            pytest.param(
                {"reference_ellipsoid": "GRS80", "scale_factor": 1.1},
                {"reference_ellipsoid": "GRS80"},
                id="ignored2",
            ),
        ),
    )
    def test_transform_ellipsoid_parameters(self, mapping, expected):
        actual = map_projection.transform_ellipsoid_parameters(mapping)

        assert actual == expected

    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param(
                {
                    "map_origin": {"a": 1, "b": 2},
                    "standard_parallel": {"phi1": 1, "phi2": 2},
                    "standard_parallel2": {"param1": 1, "param2": 2},
                    "central_meridian": {"param1": 0, "param2": 1, "param3": 2},
                },
                {"standard_parallel": {"phi1": 1, "phi2": 2}},
                id="ignored",
            ),
        ),
    )
    def test_transform_projection(self, mapping, expected):
        actual = map_projection.transform_projection(mapping)

        assert actual == expected

    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param(
                {
                    "projected": {
                        "top_left_corner": {
                            "northing": (7.5, {"units": "m"}),
                            "easting": (10.0, {"units": "m"}),
                        },
                        "top_right_corner": {
                            "northing": (7.5, {"units": "m"}),
                            "easting": (12.0, {"units": "m"}),
                        },
                        "bottom_right_corner": {
                            "northing": (6.5, {"units": "m"}),
                            "easting": (12.0, {"units": "m"}),
                        },
                        "bottom_left_corner": {
                            "northing": (6.5, {"units": "m"}),
                            "easting": (10.0, {"units": "m"}),
                        },
                    }
                },
                {
                    "projected": {
                        "corner": (
                            ["corner"],
                            ["top_left", "top_right", "bottom_right", "bottom_left"],
                            {},
                        ),
                        "northing": (["corner"], [7.5, 7.5, 6.5, 6.5], {"units": "m"}),
                        "easting": (["corner"], [10.0, 12.0, 12.0, 10.0], {"units": "m"}),
                    }
                },
                id="projected",
            ),
            pytest.param(
                {
                    "geographic": {
                        "top_left_corner": {
                            "latitude": (7.5, {"units": "deg"}),
                            "longitude": (10.0, {"units": "deg"}),
                        },
                        "top_right_corner": {
                            "latitude": (7.5, {"units": "deg"}),
                            "longitude": (12.0, {"units": "deg"}),
                        },
                        "bottom_right_corner": {
                            "latitude": (6.5, {"units": "deg"}),
                            "longitude": (12.0, {"units": "deg"}),
                        },
                        "bottom_left_corner": {
                            "latitude": (6.5, {"units": "deg"}),
                            "longitude": (10.0, {"units": "deg"}),
                        },
                    }
                },
                {
                    "geographic": {
                        "corner": (
                            ["corner"],
                            ["top_left", "top_right", "bottom_right", "bottom_left"],
                            {},
                        ),
                        "latitude": (["corner"], [7.5, 7.5, 6.5, 6.5], {"units": "deg"}),
                        "longitude": (["corner"], [10.0, 12.0, 12.0, 10.0], {"units": "deg"}),
                    }
                },
                id="geographic",
            ),
            pytest.param(
                {
                    "terrain_heights_relative_to_ellipsoid": {
                        "top_left_corner": (1.2, {"units": "m"}),
                        "top_right_corner": (1.3, {"units": "m"}),
                        "bottom_right_corner": (1.1, {"units": "m"}),
                        "bottom_left_corner": (1.0, {"units": "m"}),
                    }
                },
                {},
                id="ignored",
            ),
        ),
    )
    def test_transform_corner_points(self, mapping, expected):
        actual = map_projection.transform_corner_points(mapping)

        assert actual == expected

    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param(
                {"a": ({"a1": 1, "a2": 2}, {"abc": "def"})},
                {
                    "a": (
                        {
                            "names": ("names", ["a1", "a2"], {}),
                            "coefficients": ("names", [1, 2], {}),
                        },
                        {"abc": "def"},
                    )
                },
                id="reordering",
            ),
            pytest.param(
                {
                    "map_projection_to_pixels": ({"a": 1}, {}),
                    "pixels_to_map_projection": ({"a": 1}, {}),
                },
                {
                    "projected_to_image": (
                        {"names": ("names", ["a"], {}), "coefficients": ("names", [1], {})},
                        {},
                    ),
                    "image_to_projected": (
                        {"names": ("names", ["a"], {}), "coefficients": ("names", [1], {})},
                        {},
                    ),
                },
                id="renaming",
            ),
        ),
    )
    def test_transform_conversion_coefficients(self, mapping, expected):
        actual = map_projection.transform_conversion_coefficients(mapping)

        assert actual == expected

    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param(
                {"spare1": "", "blanks10": "", "a": {}},
                Group(
                    path=None,
                    url=None,
                    data={"a": Group(path=None, url=None, data={}, attrs={})},
                    attrs={},
                ),
                id="spares",
            ),
            pytest.param(
                {"preamble": {}}, Group(path=None, url=None, data={}, attrs={}), id="ignored"
            ),
            pytest.param(
                {
                    "map_projection_designator": "UTM-PROJECTION",
                    "utm_projection": {"type": "UNIVERSAL TRANSVERSE MERCATOR"},
                    "ups_projection": {"type": ""},
                    "national_system_projection": {"map_projection_description": ""},
                },
                Group(
                    path=None,
                    url=None,
                    data={
                        "projection": Group(
                            path=None,
                            url=None,
                            data={},
                            attrs={"type": "UNIVERSAL TRANSVERSE MERCATOR"},
                        )
                    },
                    attrs={},
                ),
                id="filtered",
            ),
            pytest.param(
                {"conversion_coefficients": {"a": ({"a1": 1, "a2": 2}, {"abc": "def"})}},
                Group(
                    path=None,
                    url=None,
                    data={
                        "conversion_coefficients": Group(
                            path=None,
                            url=None,
                            data={
                                "a": Group(
                                    path=None,
                                    url=None,
                                    data={
                                        "names": Variable("names", ["a1", "a2"], {}),
                                        "coefficients": Variable("names", [1, 2], {}),
                                    },
                                    attrs={"abc": "def"},
                                )
                            },
                            attrs={},
                        )
                    },
                    attrs={},
                ),
                id="transformed",
            ),
            pytest.param(
                {
                    "map_projection_general_information": {},
                    "map_projection_ellipsoid_parameters": {},
                },
                Group(
                    path=None,
                    url=None,
                    data={
                        "general_information": Group(path=None, url=None, data={}, attrs={}),
                        "ellipsoid_parameters": Group(path=None, url=None, data={}, attrs={}),
                    },
                    attrs={},
                ),
                id="renamed",
            ),
        ),
    )
    def test_transform_map_projection(self, mapping, expected):
        actual = map_projection.transform_map_projection(mapping)

        assert_identical(actual, expected)


class TestPlatformPositions:
    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param({"date": "2011  07  16", "seconds_of_day": 0}, "2011-07-16T00:00:00"),
            pytest.param({"date": "2021  12  31", "seconds_of_day": 81431}, "2021-12-31T22:37:11"),
        ),
    )
    def test_composite_datetime(self, mapping, expected):
        actual = platform_position.transform_composite_datetime(mapping)

        assert actual == expected

    @pytest.mark.parametrize(
        ["elements", "expected"],
        (
            pytest.param(
                [
                    {
                        "position": {
                            "x": (1, {"units": "m"}),
                            "y": (1, {"units": "m"}),
                            "z": (1, {"units": "m"}),
                        }
                    },
                    {
                        "position": {
                            "x": (2, {"units": "m"}),
                            "y": (2, {"units": "m"}),
                            "z": (2, {"units": "m"}),
                        }
                    },
                    {
                        "position": {
                            "x": (3, {"units": "m"}),
                            "y": (3, {"units": "m"}),
                            "z": (3, {"units": "m"}),
                        }
                    },
                ],
                {
                    "position": {
                        "x": (["positions"], [1, 2, 3], {"units": "m"}),
                        "y": (["positions"], [1, 2, 3], {"units": "m"}),
                        "z": (["positions"], [1, 2, 3], {"units": "m"}),
                    }
                },
                id="position",
            ),
            pytest.param(
                [
                    {
                        "velocity": {
                            "x": (2, {"units": "m/s"}),
                            "y": (3, {"units": "m/s"}),
                            "z": (1, {"units": "m/s"}),
                        }
                    },
                    {
                        "velocity": {
                            "x": (3, {"units": "m/s"}),
                            "y": (2, {"units": "m/s"}),
                            "z": (2, {"units": "m/s"}),
                        }
                    },
                    {
                        "velocity": {
                            "x": (4, {"units": "m/s"}),
                            "y": (3, {"units": "m/s"}),
                            "z": (1, {"units": "m/s"}),
                        }
                    },
                ],
                {
                    "velocity": {
                        "x": (["positions"], [2, 3, 4], {"units": "m/s"}),
                        "y": (["positions"], [3, 2, 3], {"units": "m/s"}),
                        "z": (["positions"], [1, 2, 1], {"units": "m/s"}),
                    }
                },
                id="velocity",
            ),
        ),
    )
    def test_transform_positions(self, elements, expected):
        actual = platform_position.transform_positions(elements)

        assert actual == expected

    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param(
                {"preamble": {}, "number_of_data_points": 28, "greenwich_mean_hour_angle": 0},
                Group(path=None, url=None, data={}, attrs={}),
                id="ignored",
            ),
            pytest.param(
                {"spare10": ""}, Group(path=None, url=None, data={}, attrs={}), id="spares"
            ),
            pytest.param(
                {
                    "datetime_of_first_point": {
                        "date": "2011  07  16",
                        "day_of_year": "197",
                        "seconds_of_day": 0,
                    },
                    "occurrence_flag_of_a_leap_second": 0,
                },
                Group(
                    path=None,
                    url=None,
                    data={},
                    attrs={"datetime_of_first_point": "2011-07-16T00:00:00", "leap_second": False},
                ),
                id="transformed1",
            ),
            pytest.param(
                {
                    "positions": [
                        {
                            "position": {
                                "x": (1, {"units": "m"}),
                                "y": (1, {"units": "m"}),
                                "z": (1, {"units": "m"}),
                            },
                            "velocity": {
                                "x": (4, {"units": "m/s"}),
                                "y": (3, {"units": "m/s"}),
                                "z": (6, {"units": "m/s"}),
                            },
                        }
                    ]
                },
                Group(
                    path=None,
                    url=None,
                    data={
                        "positions": Group(
                            path=None,
                            url=None,
                            data={
                                "position": Group(
                                    path=None,
                                    url=None,
                                    data={
                                        "x": Variable(["positions"], [1], {"units": "m"}),
                                        "y": Variable(["positions"], [1], {"units": "m"}),
                                        "z": Variable(["positions"], [1], {"units": "m"}),
                                    },
                                    attrs={},
                                ),
                                "velocity": Group(
                                    path=None,
                                    url=None,
                                    data={
                                        "x": Variable(["positions"], [4], {"units": "m/s"}),
                                        "y": Variable(["positions"], [3], {"units": "m/s"}),
                                        "z": Variable(["positions"], [6], {"units": "m/s"}),
                                    },
                                    attrs={},
                                ),
                            },
                            attrs={},
                        )
                    },
                    attrs={},
                ),
                id="transformed2",
            ),
            pytest.param(
                {
                    "occurrence_flag_of_a_leap_second": 1,
                    "time_interval_between_data_points": (60.0, {"units": "s"}),
                },
                Group(
                    path=None,
                    url=None,
                    data={"sampling_frequency": Variable((), 60.0, {"units": "s"})},
                    attrs={"leap_second": True},
                ),
                id="renamed",
            ),
            pytest.param(
                {"orbital_elements_designator": "high_precision"},
                Group(
                    path=None,
                    url=None,
                    data={
                        "orbital_elements": Group(
                            path=None, url=None, data={}, attrs={"type": "high_precision"}
                        )
                    },
                    attrs={},
                ),
                id="moved",
            ),
        ),
    )
    def test_transform_platform_position(self, mapping, expected):
        actual = platform_position.transform_platform_position(mapping)

        assert_identical(actual, expected)


class TestAttitude:
    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param(
                {"day_of_year": [0, 1], "millisecond_of_day": [548, 749]},
                np.array([548000000, 86400749000000], dtype="timedelta64[ns]"),
            ),
            pytest.param(
                {"day_of_year": [9], "millisecond_of_day": [698]},
                np.array([777600698000000], dtype="timedelta64[ns]"),
            ),
        ),
    )
    def test_transform_time(self, mapping, expected):
        actual = attitude.transform_time(mapping)

        np.testing.assert_equal(actual, expected)

    @pytest.mark.parametrize(
        ["dim", "var", "expected"],
        (
            pytest.param("x", 1, ("x", 1, {})),
            pytest.param("x", (1, {"b": 1}), ("x", 1, {"b": 1})),
            pytest.param("x", {"a": 1}, {"a": ("x", 1, {})}),
        ),
    )
    def test_prepend_dim(self, dim, var, expected):
        actual = attitude.prepend_dim(dim, var)

        assert actual == expected

    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param(
                {
                    "roll": [(1, {"units": "deg"}), (2, {"units": "deg"})],
                    "pitch": [(2, {"units": "deg"}), (3, {"units": "deg"})],
                    "yaw": [(3, {"units": "deg"}), (4, {"units": "deg"})],
                },
                {
                    "roll": ([1, 2], {"units": "deg"}),
                    "pitch": ([2, 3], {"units": "deg"}),
                    "yaw": ([3, 4], {"units": "deg"}),
                },
            ),
            pytest.param(
                {"roll_error": [0, 1], "pitch_error": [1, 0], "yaw_error": [1, 1]},
                {
                    "roll_error": [False, True],
                    "pitch_error": [True, False],
                    "yaw_error": [True, True],
                },
            ),
        ),
    )
    def test_transform_section(self, mapping, expected):
        actual = attitude.transform_section(mapping)

        assert actual == expected

    @pytest.mark.parametrize(
        ["raw_points", "expected"],
        (
            pytest.param(
                [
                    {"a": {"b": 1, "c": 2}, "d": {"e": 3}},
                    {"a": {"b": 2, "c": 3}, "d": {"e": 4}},
                    {"a": {"b": 3, "c": 4}, "d": {"e": 5}},
                ],
                Group(
                    path=None,
                    url=None,
                    data={
                        "a": Group(
                            path=None,
                            url=None,
                            data={
                                "b": Variable(["points"], [1, 2, 3], {}),
                                "c": Variable(["points"], [2, 3, 4], {}),
                            },
                            attrs={"coordinates": ["time"]},
                        ),
                        "d": Group(
                            path=None,
                            url=None,
                            data={"e": Variable(["points"], [3, 4, 5], {})},
                            attrs={"coordinates": ["time"]},
                        ),
                    },
                    attrs={},
                ),
                id="transformed",
            ),
            pytest.param(
                [
                    {"time": {"day_of_year": 0, "millisecond_of_day": 10}},
                    {"time": {"day_of_year": 0, "millisecond_of_day": 11}},
                    {"time": {"day_of_year": 0, "millisecond_of_day": 12}},
                    {"time": {"day_of_year": 0, "millisecond_of_day": 13}},
                ],
                Group(
                    path=None,
                    url=None,
                    data={
                        "attitude": Group(
                            path=None,
                            url=None,
                            data={
                                "time": Variable(
                                    ["points"],
                                    np.array(
                                        [10000000, 11000000, 12000000, 13000000],
                                        dtype="timedelta64[ns]",
                                    ),
                                    {},
                                )
                            },
                            attrs={"coordinates": ["time"]},
                        ),
                        "rates": Group(
                            path=None,
                            url=None,
                            data={
                                "time": Variable(
                                    ["points"],
                                    np.array(
                                        [10000000, 11000000, 12000000, 13000000],
                                        dtype="timedelta64[ns]",
                                    ),
                                    {},
                                )
                            },
                            attrs={"coordinates": ["time"]},
                        ),
                    },
                    attrs={},
                ),
                id="time",
            ),
        ),
    )
    def test_transform_attitude(self, raw_points, expected):
        mapping = {"data_points": raw_points}

        actual = attitude.transform_attitude(mapping)

        assert_identical(actual, expected)


class TestRadiometricData:
    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param(
                {"a": {"a": 0, "b": 1, "c": 2, "d": 3}},
                (
                    {
                        "a": (["i", "j"], [[0, 1], [2, 3]], {}),
                        "i": (
                            "i",
                            ["horizontal", "vertical"],
                            {"long_name": "reception polarization"},
                        ),
                        "j": (
                            "j",
                            ["horizontal", "vertical"],
                            {"long_name": "transmission polarization"},
                        ),
                    },
                    {},
                ),
            ),
            pytest.param(
                ({"a": {"a": 0, "b": 1, "c": 2, "d": 3}}, {"a": "def"}),
                (
                    {
                        "a": (["i", "j"], [[0, 1], [2, 3]], {}),
                        "i": (
                            "i",
                            ["horizontal", "vertical"],
                            {"long_name": "reception polarization"},
                        ),
                        "j": (
                            "j",
                            ["horizontal", "vertical"],
                            {"long_name": "transmission polarization"},
                        ),
                    },
                    {"a": "def"},
                ),
            ),
            pytest.param(
                {
                    "a": {"a": 1j, "b": 2j, "c": 3j, "d": 4j},
                    "b": {"f": 0j, "e": 1j, "d": 2j, "c": 3j},
                },
                (
                    {
                        "a": (["i", "j"], [[1j, 2j], [3j, 4j]], {}),
                        "b": (["i", "j"], [[0j, 1j], [2j, 3j]], {}),
                        "i": (
                            "i",
                            ["horizontal", "vertical"],
                            {"long_name": "reception polarization"},
                        ),
                        "j": (
                            "j",
                            ["horizontal", "vertical"],
                            {"long_name": "transmission polarization"},
                        ),
                    },
                    {},
                ),
            ),
        ),
    )
    def test_transform_matrices(self, mapping, expected):
        actual = radiometric_data.transform_matrices(mapping)

        assert actual == expected

    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param(
                {
                    "preamble": "",
                    "radiometric_data_records_sequence_number": 0,
                    "number_of_radiometric_fields": 1,
                    "blanks": "",
                },
                Group(path=None, url=None, data={}, attrs={}),
                id="ignored",
            ),
            pytest.param(
                {"calibration_factor": (-10.0, {"formula": "abc"})},
                Group(
                    path=None,
                    url=None,
                    data={"calibration_factor": Variable((), -10.0, {"formula": "abc"})},
                    attrs={},
                ),
                id="calibration_factor",
            ),
            pytest.param(
                {
                    "distortion_matrix": (
                        {
                            "a": {"a": 1, "b": 2, "c": 3, "d": 4},
                            "b": {"f": 0, "e": 1, "d": 2, "c": 3},
                        },
                        {"formula": "def"},
                    )
                },
                Group(
                    path=None,
                    url=None,
                    data={
                        "distortion_matrix": Group(
                            path=None,
                            url=None,
                            data={
                                "a": Variable(["i", "j"], [[1, 2], [3, 4]], {}),
                                "b": Variable(["i", "j"], [[0, 1], [2, 3]], {}),
                                "i": Variable(
                                    ["i"],
                                    ["horizontal", "vertical"],
                                    {"long_name": "reception polarization"},
                                ),
                                "j": Variable(
                                    ["j"],
                                    ["horizontal", "vertical"],
                                    {"long_name": "transmission polarization"},
                                ),
                            },
                            attrs={"formula": "def"},
                        )
                    },
                    attrs={},
                ),
                id="distortion_matrix",
            ),
        ),
    )
    def test_transform_radiometric_data(self, mapping, expected):
        actual = radiometric_data.transform_radiometric_data(mapping)

        assert_identical(actual, expected)


class TestDataQualitySummary:
    @pytest.mark.parametrize(
        ["mapping", "key", "expected"],
        (
            pytest.param(
                {
                    "a": [
                        {"b": (1, {"u": "v"}), "c": (-1, {"u": "v"})},
                        {"b": (2, {"u": "v"}), "c": (-2, {"u": "v"})},
                    ]
                },
                "a",
                {"b": ("channel", [1, 2], {"u": "v"}), "c": ("channel", [-1, -2], {"u": "v"})},
            ),
            pytest.param(
                {"f1": [{"r": 1, "o": (-1, {"a": "e"})}, {"r": 2, "o": (-2, {"a": "e"})}]},
                "f1",
                {"r": ("channel", [1, 2], {}), "o": ("channel", [-1, -2], {"a": "e"})},
            ),
        ),
    )
    def test_transform_relative(self, mapping, key, expected):
        actual = data_quality_summary.transform_relative(mapping, key)

        assert actual == expected

    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param(
                {"a": {"spare1": ""}, "blanks": ""},
                Group(
                    path=None,
                    url=None,
                    data={"a": Group(path=None, url=None, data={}, attrs={})},
                    attrs={},
                ),
                id="spares",
            ),
            pytest.param(
                {"preamble": {}, "record_number": 1},
                Group(path=None, url=None, data={}, attrs={}),
                id="ignored",
            ),
            pytest.param(
                {
                    "relative_radiometric_quality": {
                        "nominal_relative_radiometric_calibration_uncertainty": [{"a": 1}, {"a": 2}]
                    },
                    "relative_geometric_quality": {
                        "relative_misregistration_error": [
                            {"b": (-1, {"b": 1})},
                            {"b": (-2, {"b": 1})},
                            {"b": (-3, {"b": 1})},
                        ]
                    },
                },
                Group(
                    path=None,
                    url=None,
                    data={
                        "relative_radiometric_quality": Group(
                            path=None,
                            url=None,
                            data={"a": Variable("channel", [1, 2], {})},
                            attrs={},
                        ),
                        "relative_geometric_quality": Group(
                            path=None,
                            url=None,
                            data={"b": Variable("channel", [-1, -2, -3], {"b": 1})},
                            attrs={},
                        ),
                    },
                    attrs={},
                ),
                id="transformed",
            ),
        ),
    )
    def test_transform_data_quality_summary(self, mapping, expected):
        actual = data_quality_summary.transform_data_quality_summary(mapping)

        assert_identical(actual, expected)


class TestFacilityRelatedData:
    @pytest.mark.parametrize(
        ["mapping", "dim", "expected"],
        (
            pytest.param(
                ({"a": [1, 2]}, {"u": "v"}),
                "dim",
                ({"a": ("dim", [1, 2], {})}, {"u": "v"}),
                id="array",
            ),
            pytest.param(({"b": 1.0}, {}), "dim", ({"b": ((), 1.0, {})}, {}), id="scalar"),
        ),
    )
    def test_transform_group(self, mapping, dim, expected):
        actual = facility_related_data.transform_group(mapping, dim)

        assert actual == expected

    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param(
                {
                    "preamble": {},
                    "spare11": "",
                    "blanks4": "",
                    "record_sequence_number": 1,
                    "system_reserve": "",
                },
                Group(path=None, url=None, data={}, attrs={}),
                id="ignored",
            ),
            pytest.param(
                {"prf_switching_flag": 0},
                Group(path=None, url=None, data={}, attrs={"prf_switching": False}),
                id="transformed1",
            ),
            pytest.param(
                {
                    "conversion_from_map_projection_to_pixel": (
                        {"a": [1, 2], "b": [3, 4]},
                        {"a": "b"},
                    )
                },
                Group(
                    path=None,
                    url=None,
                    data={
                        "projected_to_image": Group(
                            path=None,
                            url=None,
                            data={
                                "a": Variable("mid_precision_coeffs", [1, 2], {}),
                                "b": Variable("mid_precision_coeffs", [3, 4], {}),
                            },
                            attrs={"a": "b"},
                        )
                    },
                    attrs={},
                ),
                id="transformed2",
            ),
            pytest.param(
                {"conversion_from_pixel_to_geographic": ({"a": [1, 2], "b": 1.0}, {"d": "e"})},
                Group(
                    path=None,
                    url=None,
                    data={
                        "image_to_geographic": Group(
                            path=None,
                            url=None,
                            data={
                                "a": Variable("high_precision_coeffs", [1, 2], {}),
                                "b": Variable((), 1.0, {}),
                            },
                            attrs={"d": "e"},
                        )
                    },
                    attrs={},
                ),
                id="transformed3",
            ),
            pytest.param(
                {"conversion_from_geographic_to_pixel": ({"c": [1, 2], "d": 1.0}, {"f": "e"})},
                Group(
                    path=None,
                    url=None,
                    data={
                        "geographic_to_image": Group(
                            path=None,
                            url=None,
                            data={
                                "c": Variable("high_precision_coeffs", [1, 2], {}),
                                "d": Variable((), 1.0, {}),
                            },
                            attrs={"f": "e"},
                        )
                    },
                    attrs={},
                ),
                id="transformed4",
            ),
        ),
    )
    def test_transform_record5(self, mapping, expected):
        actual = facility_related_data.transform_record5(mapping)

        assert_identical(actual, expected)


class TestMetadata:
    @pytest.mark.parametrize(
        ["group", "expected"],
        (
            pytest.param(
                Group(
                    path=None,
                    url=None,
                    data={"attitude": Group(path=None, url=None, data={}, attrs={})},
                    attrs={},
                ),
                Group(
                    path=None,
                    url=None,
                    data={"attitude": Group(path=None, url=None, data={}, attrs={})},
                    attrs={},
                ),
                id="without_platform_position",
            ),
            pytest.param(
                Group(
                    path=None,
                    url=None,
                    data={"platform_position": Group(path=None, url=None, data={}, attrs={})},
                    attrs={},
                ),
                Group(
                    path=None,
                    url=None,
                    data={"platform_position": Group(path=None, url=None, data={}, attrs={})},
                    attrs={},
                ),
                id="without_attitude",
            ),
            pytest.param(
                Group(path=None, url=None, data={}, attrs={}),
                Group(path=None, url=None, data={}, attrs={}),
                id="without_either",
            ),
            pytest.param(
                Group(
                    path=None,
                    url=None,
                    data={
                        "platform_position": Group(
                            path=None,
                            url=None,
                            data={},
                            attrs={"datetime_of_first_point": "2012-11-10T01:31:54"},
                        ),
                        "attitude": Group(
                            path=None,
                            url=None,
                            data={
                                "positions": Group(
                                    path=None,
                                    url=None,
                                    data={
                                        "time": Variable(
                                            "points",
                                            np.array(
                                                [3600000000000, 7200000000000],
                                                dtype="timedelta64[ns]",
                                            ),
                                            {},
                                        )
                                    },
                                    attrs={},
                                )
                            },
                            attrs={},
                        ),
                    },
                    attrs={},
                ),
                Group(
                    path=None,
                    url=None,
                    data={
                        "platform_position": Group(
                            path=None,
                            url=None,
                            data={},
                            attrs={"datetime_of_first_point": "2012-11-10T01:31:54"},
                        ),
                        "attitude": Group(
                            path=None,
                            url=None,
                            data={
                                "positions": Group(
                                    path=None,
                                    url=None,
                                    data={
                                        "time": Variable(
                                            "points",
                                            np.array(
                                                [
                                                    "2012-01-01T01:00:00.000000000",
                                                    "2012-01-01T02:00:00.000000000",
                                                ],
                                                dtype="datetime64[ns]",
                                            ),
                                            {},
                                        )
                                    },
                                    attrs={},
                                )
                            },
                            attrs={},
                        ),
                    },
                    attrs={},
                ),
                id="fixed1",
            ),
            pytest.param(
                Group(
                    path=None,
                    url=None,
                    data={
                        "platform_position": Group(
                            path=None,
                            url=None,
                            data={},
                            attrs={"datetime_of_first_point": "1986-05-24T16:52:01"},
                        ),
                        "attitude": Group(
                            path=None,
                            url=None,
                            data={
                                "positions": Group(
                                    path=None,
                                    url=None,
                                    data={
                                        "time": Variable(
                                            "points",
                                            np.array(
                                                [19329831000000000, 20467200000000000],
                                                dtype="timedelta64[ns]",
                                            ),
                                            {},
                                        )
                                    },
                                    attrs={},
                                ),
                                "velocity": Group(
                                    path=None,
                                    url=None,
                                    data={
                                        "time": Variable(
                                            "points",
                                            np.array(
                                                [19329831000000000, 20467200000000000],
                                                dtype="timedelta64[ns]",
                                            ),
                                            {},
                                        )
                                    },
                                    attrs={},
                                ),
                            },
                            attrs={},
                        ),
                    },
                    attrs={},
                ),
                Group(
                    path=None,
                    url=None,
                    data={
                        "platform_position": Group(
                            path=None,
                            url=None,
                            data={},
                            attrs={"datetime_of_first_point": "1986-05-24T16:52:01"},
                        ),
                        "attitude": Group(
                            path=None,
                            url=None,
                            data={
                                "positions": Group(
                                    path=None,
                                    url=None,
                                    data={
                                        "time": Variable(
                                            "points",
                                            np.array(
                                                [
                                                    "1986-08-12T17:23:51.000000000",
                                                    "1986-08-25T21:20:00.000000000",
                                                ],
                                                dtype="datetime64[ns]",
                                            ),
                                            {},
                                        )
                                    },
                                    attrs={},
                                ),
                                "velocity": Group(
                                    path=None,
                                    url=None,
                                    data={
                                        "time": Variable(
                                            "points",
                                            np.array(
                                                [
                                                    "1986-08-12T17:23:51.000000000",
                                                    "1986-08-25T21:20:00.000000000",
                                                ],
                                                dtype="datetime64[ns]",
                                            ),
                                            {},
                                        )
                                    },
                                    attrs={},
                                ),
                            },
                            attrs={},
                        ),
                    },
                    attrs={},
                ),
                id="fixed2",
            ),
        ),
    )
    def test_fix_attitude_time(self, group, expected):
        actual = metadata.fix_attitude_time(group)

        assert_identical(actual, expected)

    @pytest.mark.parametrize(
        ["mapping", "expected"],
        (
            pytest.param(
                {
                    "file_descriptor": {"a": ""},
                    "facility_related_data_1": {},
                    "facility_related_data_2": {},
                    "facility_related_data_3": {},
                    "facility_related_data_4": {},
                },
                Group(path=None, url=None, data={}, attrs={}),
                id="ignored",
            ),
            pytest.param(
                {"map_projection": []},
                Group(path=None, url=None, data={}, attrs={}),
                id="empty-items",
            ),
            pytest.param(
                {"dataset_summary": {"scene_center_time": "2020101117213774"}},
                Group(
                    path=None,
                    url=None,
                    data={
                        "dataset_summary": Group(
                            path=None,
                            url=None,
                            data={},
                            attrs={"scene_center_time": "2020-10-11T17:21:37.740000"},
                        )
                    },
                    attrs={},
                ),
                id="transformed-dataset_summary",
            ),
            pytest.param(
                {"map_projection": [{"map_projection_general_information": {}}]},
                Group(
                    path=None,
                    url=None,
                    data={
                        "map_projection": Group(
                            path=None,
                            url=None,
                            data={
                                "general_information": Group(path=None, url=None, data={}, attrs={})
                            },
                            attrs={},
                        )
                    },
                    attrs={},
                ),
                id="transformed-map_projection",
            ),
            pytest.param(
                {"platform_position": {"occurrence_flag_of_a_leap_second": True}},
                Group(
                    path=None,
                    url=None,
                    data={
                        "platform_position": Group(
                            path=None, url=None, data={}, attrs={"leap_second": True}
                        )
                    },
                    attrs={},
                ),
                id="transformed-platform_position",
            ),
            pytest.param(
                {
                    "attitude": {
                        "data_points": [
                            {"a": {"b": 1, "c": 2}},
                            {"a": {"b": 2, "c": 3}},
                            {"a": {"b": 3, "c": 4}},
                        ]
                    }
                },
                Group(
                    path=None,
                    url=None,
                    data={
                        "attitude": Group(
                            path=None,
                            url=None,
                            data={
                                "a": Group(
                                    path=None,
                                    url=None,
                                    data={
                                        "b": Variable(["points"], [1, 2, 3], {}),
                                        "c": Variable(["points"], [2, 3, 4], {}),
                                    },
                                    attrs={"coordinates": ["time"]},
                                )
                            },
                            attrs={},
                        )
                    },
                    attrs={},
                ),
                id="transformed-attitude",
            ),
            pytest.param(
                {"radiometric_data": {"calibration_factor": (-10.0, {"formula": "abc"})}},
                Group(
                    path=None,
                    url=None,
                    data={
                        "radiometric_data": Group(
                            path=None,
                            url=None,
                            data={"calibration_factor": Variable((), -10.0, {"formula": "abc"})},
                            attrs={},
                        )
                    },
                    attrs={},
                ),
                id="transformed-radiometric_data",
            ),
            pytest.param(
                {"data_quality_summary": {"number_of_channels": 8, "record_number": 1}},
                Group(
                    path=None,
                    url=None,
                    data={
                        "data_quality_summary": Group(
                            path=None, url=None, data={}, attrs={"number_of_channels": 8}
                        )
                    },
                    attrs={},
                ),
                id="transformed-data_quality_summary",
            ),
            pytest.param(
                {"facility_related_data_5": {"prf_switching_flag": 1}},
                Group(
                    path=None,
                    url=None,
                    data={
                        "transformations": Group(
                            path=None, url=None, data={}, attrs={"prf_switching": True}
                        )
                    },
                    attrs={},
                ),
                id="transformed-record5",
            ),
            pytest.param(
                {
                    "radiometric_data": {"calibration_factor": (-10.0, {"formula": "abc"})},
                    "facility_related_data_5": {"prf_switching_flag": 1},
                },
                Group(
                    path=None,
                    url=None,
                    data={
                        "radiometric_data": Group(
                            path=None,
                            url=None,
                            data={"calibration_factor": Variable((), -10.0, {"formula": "abc"})},
                            attrs={},
                        ),
                        "transformations": Group(
                            path=None, url=None, data={}, attrs={"prf_switching": True}
                        ),
                    },
                    attrs={},
                ),
                id="transformed-multiple",
            ),
            pytest.param(
                {"facility_related_data_5": {"prf_switching_flag": 1}},
                Group(
                    path=None,
                    url=None,
                    data={
                        "transformations": Group(
                            path=None, url=None, data={}, attrs={"prf_switching": True}
                        )
                    },
                    attrs={},
                ),
                id="renamed",
            ),
            pytest.param(
                {
                    "attitude": {
                        "data_points": [
                            {"time": {"day_of_year": 0, "millisecond_of_day": 10}},
                            {"time": {"day_of_year": 0, "millisecond_of_day": 11}},
                            {"time": {"day_of_year": 0, "millisecond_of_day": 12}},
                            {"time": {"day_of_year": 0, "millisecond_of_day": 13}},
                        ]
                    },
                    "platform_position": {
                        "datetime_of_first_point": {
                            "date": "2011  07  16",
                            "day_of_year": "197",
                            "seconds_of_day": 0,
                        }
                    },
                },
                Group(
                    path=None,
                    url=None,
                    data={
                        "attitude": Group(
                            path=None,
                            url=None,
                            data={
                                "attitude": Group(
                                    path=None,
                                    url=None,
                                    data={
                                        "time": Variable(
                                            "points",
                                            np.array(
                                                [
                                                    "2011-01-01T00:00:00.010",
                                                    "2011-01-01T00:00:00.011",
                                                    "2011-01-01T00:00:00.012",
                                                    "2011-01-01T00:00:00.013",
                                                ],
                                                dtype="datetime64[ns]",
                                            ),
                                            {},
                                        )
                                    },
                                    attrs={"coordinates": ["time"]},
                                ),
                                "rates": Group(
                                    path=None,
                                    url=None,
                                    data={
                                        "time": Variable(
                                            "points",
                                            np.array(
                                                [
                                                    "2011-01-01T00:00:00.010",
                                                    "2011-01-01T00:00:00.011",
                                                    "2011-01-01T00:00:00.012",
                                                    "2011-01-01T00:00:00.013",
                                                ],
                                                dtype="datetime64[ns]",
                                            ),
                                            {},
                                        )
                                    },
                                    attrs={"coordinates": ["time"]},
                                ),
                            },
                            attrs={},
                        ),
                        "platform_position": Group(
                            path=None,
                            url=None,
                            data={},
                            attrs={"datetime_of_first_point": "2011-07-16T00:00:00"},
                        ),
                    },
                    attrs={},
                ),
                id="postprocessed",
            ),
        ),
    )
    def test_transform_metadata(self, mapping, expected):
        actual = metadata.transform_metadata(mapping)

        assert_identical(actual, expected)


@pytest.mark.parametrize(
    ["path", "expected"],
    (
        pytest.param("led1", FileNotFoundError("Cannot open .+"), id="not-existing"),
        pytest.param(
            "led2",
            Group(
                path=None,
                url=None,
                data={
                    "transformations": Group(
                        path=None, url=None, data={}, attrs={"prf_switching": False}
                    )
                },
                attrs={},
            ),
            id="existing",
        ),
    ),
)
def test_open_sar_leader(monkeypatch, path, expected):
    binary = b"\x01\x03"
    mapping = {"facility_related_data_5": {"prf_switching_flag": 0}}
    recorded_binary = []

    def fake_parse_data(data):
        recorded_binary.append(data)

        return mapping

    monkeypatch.setattr(io, "parse_data", fake_parse_data)

    mapper = fsspec.get_mapper("memory://")
    mapper["led2"] = binary

    if isinstance(expected, Exception):
        with pytest.raises(type(expected), match=expected.args[0]):
            io.open_sar_leader(mapper, path)

        return

    actual = io.open_sar_leader(mapper, path)
    assert_identical(actual, expected)
