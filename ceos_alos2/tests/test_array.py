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


@pytest.mark.parametrize(
    ["indexer", "expected"],
    (
        pytest.param(2, [(2, (16, 19))], id="scalar-positive"),
        pytest.param(-1, [(3, (22, 25))], id="scalar-negative"),
        pytest.param([0, 2], [(0, (0, 3)), (2, (16, 19))], id="list-positive"),
        pytest.param([0, -1], [(0, (0, 3)), (3, (22, 25))], id="list-negative"),
        pytest.param(slice(0, 1), [(0, (0, 3))], id="slice-positive_start-positive_stop-no_step"),
        pytest.param(
            slice(2, None),
            [(2, (16, 19)), (3, (22, 25))],
            id="slice-positive_start-no_stop-no_step",
        ),
        pytest.param(
            slice(None, 2), [(0, (0, 3)), (1, (5, 8))], id="slice-no_start-postive_stop-no_step"
        ),
        pytest.param(
            slice(None, None, 2),
            [(0, (0, 3)), (2, (16, 19))],
            id="slice-no_start-no_stop-positive_step",
        ),
        pytest.param(
            slice(-1, None, -2),
            [(3, (22, 25)), (1, (5, 8))],
            id="slice-negative_start-no_stop-negative_step",
        ),
    ),
)
def test_compute_selected_ranges(indexer, expected):
    byte_ranges = [(0, 3), (5, 8), (16, 19), (22, 25)]

    actual = array.compute_selected_ranges(byte_ranges, indexer)
    assert actual == expected


@pytest.mark.parametrize(
    ["chunksize", "expected"],
    (
        pytest.param(2, {0: [(0, 3), (3, 6)], 1: [(6, 9), (9, 12)], 2: [(12, 15), (15, 18)]}),
        pytest.param(3, {0: [(0, 3), (3, 6), (6, 9)], 1: [(9, 12), (12, 15), (15, 18)]}),
    ),
)
def test_groupby_chunks(chunksize, expected):
    byte_ranges = [(0, 3), (3, 6), (6, 9), (9, 12), (12, 15), (15, 18)]

    actual = array.groupby_chunks(list(enumerate(byte_ranges)), chunksize)

    assert actual == expected


@pytest.mark.parametrize(
    ["selected", "expected"],
    (
        pytest.param(
            {0: [(0, 5), (6, 9)], 2: [(26, 28), (28, 30)]},
            [((0, 12), [(0, 5), (6, 9)]), ((26, 5), [(26, 28), (28, 30)])],
        ),
        pytest.param(
            {1: [(17, 18), (19, 23)], 3: [(38, 41), (41, 45), (46, 48)]},
            [((17, 8), [(17, 18), (19, 23)]), ((37, 10), [(38, 41), (41, 45), (46, 48)])],
        ),
    ),
)
def test_merge_chunk_info(selected, expected):
    chunk_offsets = {0: (0, 12), 1: (17, 8), 2: (26, 5), 3: (37, 10)}
    actual = array.merge_chunk_info(selected, chunk_offsets)
    assert actual == expected


@pytest.mark.parametrize(
    ["chunk_info", "expected"],
    (
        pytest.param(
            {"offset": 10, "size": 200},
            [(30, 33), (33, 36), (36, 39), (39, 42), (42, 45), (45, 48)],
        ),
        pytest.param(
            {"offset": 15, "size": 200},
            [(25, 28), (28, 31), (31, 34), (34, 37), (37, 40), (40, 43)],
        ),
    ),
)
def test_relocate_ranges(chunk_info, expected):
    byte_ranges = [(40, 43), (43, 46), (46, 49), (49, 52), (52, 55), (55, 58)]

    actual = array.relocate_ranges(chunk_info, byte_ranges)
    assert actual == (chunk_info, expected)
