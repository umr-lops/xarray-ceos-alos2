import datetime

import pytest

from alos2 import decoders


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
            id="invalid_id-invalid_date",
        ),
    ),
)
def test_decode_scene_id(scene_id, expected):
    if issubclass(type(expected), Exception):
        with pytest.raises(type(expected), match=expected.args[0]):
            decoders.decode_scene_id(scene_id)

        return

    actual = decoders.decode_scene_id(scene_id)

    assert actual == expected
