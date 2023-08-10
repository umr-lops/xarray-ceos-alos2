import pytest

from ceos_alos2.volume_directory import metadata


class TestMetadata:
    @pytest.mark.parametrize(
        ["s", "expected"],
        (
            ("1990012012563297", "1990-01-20T12:56:32.970000"),
            ("2001112923595915", "2001-11-29T23:59:59.150000"),
        ),
    )
    def test_parse_datetime(self, s, expected):
        actual = metadata.normalize_datetime(s)

        assert actual == expected
