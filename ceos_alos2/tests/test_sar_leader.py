import pytest

from ceos_alos2.hierarchy import Group, Variable
from ceos_alos2.sar_leader import dataset_summary
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
