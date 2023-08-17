import pytest

from ceos_alos2.hierarchy import Group, Variable
from ceos_alos2.sar_leader import dataset_summary, map_projection
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
                {
                    "terrain_heights_relative_to_ellipsoid": {
                        "corner": (
                            ["corner"],
                            ["top_left", "top_right", "bottom_right", "bottom_left"],
                            {},
                        ),
                        "height": (["corner"], [1.2, 1.3, 1.1, 1.0], {"units": "m"}),
                    }
                },
                id="heights",
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
