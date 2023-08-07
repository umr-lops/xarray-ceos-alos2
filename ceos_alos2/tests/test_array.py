import io

import fsspec
import pytest
from fsspec.implementations.dirfs import DirFileSystem
from tlz.itertoolz import identity

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
            {0: (0, 3), 1: (3, 9), 2: (9, 16)},
            {0: {"offset": 0, "size": 3}, 1: {"offset": 3, "size": 6}, 2: {"offset": 9, "size": 7}},
        ),
        pytest.param(
            {0: (0, 3), 1: (17, 18), 2: (31, 100)},
            {
                0: {"offset": 0, "size": 3},
                1: {"offset": 17, "size": 1},
                2: {"offset": 31, "size": 69},
            },
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


def test_extract_ranges():
    data = b"buwaox94ks"
    ranges = [(1, 3), (2, 4), (3, 4), (7, 10)]
    expected = [b"uw", b"wa", b"a", b"4ks"]

    actual = array.extract_ranges(data, ranges)
    assert actual == expected


@pytest.mark.parametrize(
    ["offset", "size"],
    (
        pytest.param(0, 10),
        pytest.param(50, 100),
        pytest.param(29, 1),
        pytest.param(240, 0),
    ),
)
def test_read_chunk(offset, size):
    data = bytes(range(256))
    f = io.BytesIO(data)

    actual = array.read_chunk(f, offset, size)
    expected = data[offset : offset + size]
    assert actual == expected


class TestArray:
    @pytest.mark.parametrize("shape", ((2, 10), (4, 10), (2, 20), (4, 20)))
    @pytest.mark.parametrize("dtype", ("uint16", "complex64"))
    @pytest.mark.parametrize("chunksize", (None, "auto", -1, 2, "80B"))
    def test_init(self, shape, dtype, chunksize):
        fs = DirFileSystem(fs=fsspec.filesystem("memory"), path="/")
        url = "image-file"

        byte_ranges = [(1, 40), (40, 80), (80, 120), (120, 160)]
        byte_ranges_ = byte_ranges[: shape[0]]

        arr = array.Array(
            fs=fs,
            url=url,
            byte_ranges=byte_ranges_,
            shape=shape,
            dtype=dtype,
            records_per_chunk=chunksize,
            parse_bytes=identity,
        )

        assert arr.url == url
        assert arr.byte_ranges == byte_ranges_
        assert arr.shape == shape
        assert arr.dtype == dtype

    @pytest.mark.parametrize(
        ["other", "expected"],
        (
            pytest.param(
                array.Array(
                    fs=DirFileSystem(fs=fsspec.filesystem("memory"), path="/a"),
                    url="image-file1",
                    byte_ranges=[(0, 40), (40, 80), (80, 120), (120, 160)],
                    shape=(4, 3),
                    dtype="uint16",
                    records_per_chunk=2,
                    parse_bytes=identity,
                ),
                True,
                id="all_equal",
            ),
            pytest.param(1, False, id="mismatching_types"),
            pytest.param(
                array.Array(
                    fs=DirFileSystem(fs=fsspec.filesystem("file"), path="/a"),
                    url="image-file1",
                    byte_ranges=[(0, 40), (40, 80), (80, 120), (120, 160)],
                    shape=(4, 3),
                    dtype="uint16",
                    records_per_chunk=2,
                    parse_bytes=identity,
                ),
                False,
                id="fs-protocol",
            ),
            pytest.param(
                array.Array(
                    fs=DirFileSystem(fs=fsspec.filesystem("memory"), path="/b"),
                    url="image-file1",
                    byte_ranges=[(0, 40), (40, 80), (80, 120), (120, 160)],
                    shape=(4, 3),
                    dtype="uint16",
                    records_per_chunk=2,
                    parse_bytes=identity,
                ),
                False,
                id="fs-path",
            ),
            pytest.param(
                array.Array(
                    fs=DirFileSystem(fs=fsspec.filesystem("memory"), path="/a"),
                    url="image-file2",
                    byte_ranges=[(0, 40), (40, 80), (80, 120), (120, 160)],
                    shape=(4, 3),
                    dtype="uint16",
                    records_per_chunk=2,
                    parse_bytes=identity,
                ),
                False,
                id="url",
            ),
            pytest.param(
                array.Array(
                    fs=DirFileSystem(fs=fsspec.filesystem("memory"), path="/a"),
                    url="image-file1",
                    byte_ranges=[(0, 20), (40, 80), (80, 120), (120, 160)],
                    shape=(4, 3),
                    dtype="uint16",
                    records_per_chunk=2,
                    parse_bytes=identity,
                ),
                False,
                id="byte_ranges",
            ),
            pytest.param(
                array.Array(
                    fs=DirFileSystem(fs=fsspec.filesystem("memory"), path="/a"),
                    url="image-file1",
                    byte_ranges=[(0, 40), (40, 80), (80, 120), (120, 160)],
                    shape=(4, 2),
                    dtype="uint16",
                    records_per_chunk=2,
                    parse_bytes=identity,
                ),
                False,
                id="shape",
            ),
            pytest.param(
                array.Array(
                    fs=DirFileSystem(fs=fsspec.filesystem("memory"), path="/a"),
                    url="image-file1",
                    byte_ranges=[(0, 40), (40, 80), (80, 120), (120, 160)],
                    shape=(4, 3),
                    dtype="uint8",
                    records_per_chunk=2,
                    parse_bytes=identity,
                ),
                False,
                id="dtype",
            ),
            pytest.param(
                array.Array(
                    fs=DirFileSystem(fs=fsspec.filesystem("memory"), path="/a"),
                    url="image-file1",
                    byte_ranges=[(0, 40), (40, 80), (80, 120), (120, 160)],
                    shape=(4, 3),
                    dtype="uint16",
                    records_per_chunk=4,
                    parse_bytes=identity,
                ),
                False,
                id="records_per_chunk",
            ),
            pytest.param(
                array.Array(
                    fs=DirFileSystem(fs=fsspec.filesystem("memory"), path="/a"),
                    url="image-file1",
                    byte_ranges=[(0, 40), (40, 80), (80, 120), (120, 160)],
                    shape=(4, 3),
                    dtype="uint16",
                    records_per_chunk=2,
                    parse_bytes=lambda x: x,
                ),
                False,
                id="byte_parser",
            ),
        ),
    )
    def test_eq(self, other, expected):
        fs = DirFileSystem(fs=fsspec.filesystem("memory"), path="/a")

        byte_ranges = [(0, 40), (40, 80), (80, 120), (120, 160)]
        arr = array.Array(
            fs=fs,
            url="image-file1",
            byte_ranges=byte_ranges,
            shape=(4, 3),
            dtype="uint16",
            records_per_chunk=2,
            parse_bytes=identity,
        )

        actual = arr == other

        assert actual == expected

    @pytest.mark.parametrize(
        ["arr", "expected"],
        (
            pytest.param(
                array.Array(
                    fs=DirFileSystem(fs=fsspec.filesystem("memory"), path="/a"),
                    url="image-file1",
                    byte_ranges=[(0, 40), (40, 80), (80, 120), (120, 160)],
                    shape=(4,),
                    dtype="uint16",
                    records_per_chunk=2,
                    parse_bytes=identity,
                ),
                1,
                id="1D",
            ),
            pytest.param(
                array.Array(
                    fs=DirFileSystem(fs=fsspec.filesystem("memory"), path="/a"),
                    url="image-file1",
                    byte_ranges=[(0, 40), (40, 80), (80, 120), (120, 160)],
                    shape=(4, 3),
                    dtype="uint16",
                    records_per_chunk=2,
                    parse_bytes=identity,
                ),
                2,
                id="2D",
            ),
            pytest.param(
                array.Array(
                    fs=DirFileSystem(fs=fsspec.filesystem("memory"), path="/a"),
                    url="image-file1",
                    byte_ranges=[(0, 40), (40, 80), (80, 120), (120, 160)],
                    shape=(4, 3, 3),
                    dtype="uint16",
                    records_per_chunk=2,
                    parse_bytes=identity,
                ),
                3,
                id="3D",
            ),
        ),
    )
    def test_ndim(self, arr, expected):
        assert arr.ndim == expected

    @pytest.mark.parametrize(
        ["arr", "expected"],
        (
            pytest.param(
                array.Array(
                    fs=DirFileSystem(fs=fsspec.filesystem("memory"), path="/a"),
                    url="image-file1",
                    byte_ranges=[(0, 40), (40, 80), (80, 120), (120, 160)],
                    shape=(4,),
                    dtype="uint16",
                    records_per_chunk=4,
                    parse_bytes=identity,
                ),
                (4,),
                id="1D-4",
            ),
            pytest.param(
                array.Array(
                    fs=DirFileSystem(fs=fsspec.filesystem("memory"), path="/a"),
                    url="image-file1",
                    byte_ranges=[(0, 40), (40, 80), (80, 120), (120, 160)],
                    shape=(4, 3),
                    dtype="uint16",
                    records_per_chunk=1,
                    parse_bytes=identity,
                ),
                (1, 3),
                id="2D-1",
            ),
            pytest.param(
                array.Array(
                    fs=DirFileSystem(fs=fsspec.filesystem("memory"), path="/a"),
                    url="image-file1",
                    byte_ranges=[(0, 40), (40, 80), (80, 120), (120, 160)],
                    shape=(4, 3),
                    dtype="uint16",
                    records_per_chunk=2,
                    parse_bytes=identity,
                ),
                (2, 3),
                id="2D-2",
            ),
            pytest.param(
                array.Array(
                    fs=DirFileSystem(fs=fsspec.filesystem("memory"), path="/a"),
                    url="image-file1",
                    byte_ranges=[(0, 40), (40, 80), (80, 120), (120, 160)],
                    shape=(4, 3),
                    dtype="uint16",
                    records_per_chunk=4,
                    parse_bytes=identity,
                ),
                (4, 3),
                id="2D-4",
            ),
            pytest.param(
                array.Array(
                    fs=DirFileSystem(fs=fsspec.filesystem("memory"), path="/a"),
                    url="image-file1",
                    byte_ranges=[(0, 40), (40, 80), (80, 120), (120, 160)],
                    shape=(4, 3, 3),
                    dtype="uint16",
                    records_per_chunk=4,
                    parse_bytes=identity,
                ),
                (4, 3, 3),
                id="3D-4",
            ),
        ),
    )
    def test_chunks(self, arr, expected):
        assert arr.chunks == expected
