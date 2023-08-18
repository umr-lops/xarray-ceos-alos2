import numpy as np
import pytest

from ceos_alos2.hierarchy import Group, Variable
from ceos_alos2.sar_leader import (
    attitude,
    dataset_summary,
    map_projection,
    platform_position,
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
        ["mapping", "expected"],
        (
            pytest.param(
                [{"a": {"b": 1, "c": 2}}, {"a": {"b": 2, "c": 3}}, {"a": {"b": 3, "c": 4}}],
                {"a": {"b": [1, 2, 3], "c": [2, 3, 4]}},
            ),
            pytest.param(
                [
                    {"a": {"b": 1, "c": 2}, "d": {"e": 3}},
                    {"a": {"b": 2, "c": 3}, "d": {"e": 4}},
                    {"a": {"b": 3, "c": 4}, "d": {"e": 5}},
                ],
                {"a": {"b": [1, 2, 3], "c": [2, 3, 4]}, "d": {"e": [3, 4, 5]}},
            ),
            pytest.param([{"a": 1}, {"a": 2}, {"a": 3}], {"a": [1, 2, 3]}),
        ),
    )
    def test_transform_nested(self, mapping, expected):
        actual = attitude.transform_nested(mapping)

        assert actual == expected

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
