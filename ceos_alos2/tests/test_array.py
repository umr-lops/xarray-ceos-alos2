import io

import fsspec
import numpy as np
import pytest
from fsspec.implementations.dirfs import DirFileSystem

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


@pytest.mark.parametrize(
    ["content", "type_code", "expected"],
    (
        pytest.param(b"\x00", "F*8", ValueError("unknown type code"), id="wrong_type_code"),
        pytest.param(
            b"\x00\x01",
            "IU2",
            np.array([1], dtype="int16"),
            id="unsigned_int",
        ),
        pytest.param(
            b"\x00\x00\x00\x00\x00\x00\x00\x00",
            "C*8",
            np.array([0 + 0j], dtype="complex64"),
            id="complex",
        ),
    ),
)
def test_parse_data(content, type_code, expected):
    if isinstance(expected, Exception):
        with pytest.raises(type(expected), match=expected.args[0]):
            array.parse_data(content, type_code)

        return

    actual = array.parse_data(content, type_code)

    np.testing.assert_allclose(actual, expected)


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
            type_code="IU2",
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
                    type_code="IU2",
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
                    type_code="IU2",
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
                    type_code="IU2",
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
                    type_code="IU2",
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
                    type_code="IU2",
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
                    type_code="IU2",
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
                    type_code="IU2",
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
                    type_code="IU2",
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
                    type_code="C*8",
                ),
                False,
                id="type_code",
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
            type_code="IU2",
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
                    type_code="IU2",
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
                    type_code="IU2",
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
                    type_code="IU2",
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
                    type_code="IU2",
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
                    type_code="IU2",
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
                    type_code="IU2",
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
                    type_code="IU2",
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
                    type_code="IU2",
                ),
                (4, 3, 3),
                id="3D-4",
            ),
        ),
    )
    def test_chunks(self, arr, expected):
        assert arr.chunks == expected

    @pytest.mark.parametrize("records_per_chunk", [1, 2, 3, 4, 5])
    @pytest.mark.parametrize(
        "indexer_0",
        (
            slice(None),
            slice(2, None),
            slice(None, 2),
            slice(-2, None),
            slice(None, -2),
            slice(None, None, 2),
            slice(None, 4, 2),
            slice(2, None, 2),
            slice(2, 4, 2),
            slice(-1, None, -1),
        ),
    )
    @pytest.mark.parametrize(
        "indexer_1",
        (
            slice(None),
            slice(2, None),
            slice(None, 2),
            slice(-2, None),
            slice(None, -2),
            slice(None, None, 2),
            slice(None, 4, 2),
            slice(2, None, 2),
            slice(2, 4, 2),
            slice(-1, None, -1),
        ),
    )
    def test_getitem(self, indexer_0, indexer_1, records_per_chunk):
        fs = DirFileSystem(fs=fsspec.filesystem("memory"), path="/")
        url = "image-file"
        data = np.arange(100, dtype="uint16").reshape(5, 20)
        type_code = "IU2"

        encoded_ = data.astype(">u2").tobytes(order="C")
        chunksize = data.shape[1] * data.dtype.itemsize
        chunks = [
            encoded_[index * chunksize : (index + 1) * chunksize] for index in range(data.shape[0])
        ]
        metadata_size = 20
        gap = b"\x00" * metadata_size
        encoded = b"".join(gap + chunk for chunk in chunks)
        byte_ranges = [
            (
                index * chunksize + metadata_size * (index + 1),
                (index + 1) * chunksize + metadata_size * (index + 1),
            )
            for index in range(data.shape[0])
        ]

        shape = data.shape
        dtype = data.dtype

        with fs.open(url, mode="wb") as f:
            f.write(encoded)

        arr = array.Array(
            fs=fs,
            url=url,
            byte_ranges=byte_ranges,
            shape=shape,
            dtype=dtype,
            type_code=type_code,
            records_per_chunk=records_per_chunk,
        )
        indexers = (indexer_0, indexer_1)

        actual = arr[indexers]
        expected = data[indexers]

        np.testing.assert_equal(actual, expected)
