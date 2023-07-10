import pytest

from ceos_alos2 import array


@pytest.mark.parametrize(
    ["sizes", "reference_size", "expected"],
    (
        pytest.param([5, 5, 5], 8, 2, id="all-equal"),
        pytest.param([4, 9, 2], 2, 1, id="unbalanced"),
        pytest.param([7, 6, 8], 19, 3, id="balanced"),
    ),
)
def test_determine_nearest_chunksize(sizes, reference_size, expected):
    actual = array.determine_nearest_chunksize(sizes, reference_size)
    assert actual == expected


@pytest.mark.parametrize(
    ["ranges", "n_chunks", "expected"],
    (
        pytest.param(
            [(0, 3), (3, 6), (6, 9), (9, 12), (12, 15), (15, 18)],
            1,
            {0: (0, 3), 1: (3, 6), 2: (6, 9), 3: (9, 12), 4: (12, 15), 5: (15, 18)},
        ),
        pytest.param(
            [(0, 3), (3, 6), (6, 9), (9, 12), (12, 15), (15, 18)],
            2,
            {0: (0, 6), 1: (6, 12), 2: (12, 18)},
        ),
        pytest.param(
            [(0, 3), (3, 6), (6, 9), (9, 12), (12, 15), (15, 18)], 3, {0: (0, 9), 1: (9, 18)}
        ),
    ),
)
def test_compute_chunk_ranges(ranges, n_chunks, expected):
    actual = array.compute_chunk_ranges(ranges, n_chunks)

    assert actual == expected


@pytest.mark.parametrize(
    ["ranges", "expected"],
    (
        pytest.param(
            [(0, 3), (3, 9), (9, 16)],
            [{"offset": 0, "size": 3}, {"offset": 3, "size": 6}, {"offset": 9, "size": 7}],
        ),
        pytest.param(
            [(0, 3), (17, 18), (31, 100)],
            [{"offset": 0, "size": 3}, {"offset": 17, "size": 1}, {"offset": 31, "size": 69}],
        ),
    ),
)
def test_to_offset_size(ranges, expected):
    actual = array.to_offset_size(ranges)
    assert actual == expected
