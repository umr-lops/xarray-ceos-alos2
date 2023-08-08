from pathlib import Path

import pytest

from ceos_alos2.sar_image import caching
from ceos_alos2.sar_image.caching.path import project_name


def test_hashsum():
    # no need to verify the external library extensively
    data = "ddeeaaddbbeeeeff"
    expected = "b8be84665c5cd09ec19677ce9714bcd987422de886ac2e8432a3e2311b5f0cde"

    actual = caching.path.hashsum(data)

    assert actual == expected


@pytest.mark.parametrize(
    "cache_dir",
    [
        Path("/path/to/cache1") / project_name,
        Path("/path/to/cache2") / project_name,
    ],
)
@pytest.mark.parametrize(
    ["remote_root", "path", "expected"],
    (
        pytest.param(
            "http://127.0.0.1/path/to/data",
            "image1",
            Path("c9db4f27e586452c6517524752dc472863ee42230ba98e83a346b8da94a33235/image1.index"),
        ),
        pytest.param(
            "s3://bucket/path/to/data",
            "image1",
            Path("04391cfcf37045b78e7b4793392821b5b4c84591edfcb475954130eb34b87366/image1.index"),
        ),
        pytest.param(
            "file:///path/to/data",
            "image1",
            Path("9506f2b2ddfa8498bc4c1d3cc50d02ee5f799f6716710ff4dd31a9f6e41eac45/image1.index"),
        ),
        pytest.param(
            "/path/to/data",
            "image2",
            Path("7b405676e8ed8556a3f4f98f4dc5b6df940f3a5ce48674046eebda551e335b37/image2.index"),
        ),
    ),
)
def test_local_cache_location(monkeypatch, cache_dir, remote_root, path, expected):
    monkeypatch.setattr(caching.path, "cache_root", cache_dir)

    actual = caching.path.local_cache_location(remote_root, path)

    assert cache_dir in actual.parents
    assert actual.relative_to(cache_dir) == expected


@pytest.mark.parametrize(
    "remote_root", ("http://127.0.0.1/path/to/data", "s3://bucket/path/to/data")
)
@pytest.mark.parametrize(
    ["path", "expected"],
    (
        ("image1", "image1.index"),
        ("image7", "image7.index"),
    ),
)
def test_remote_cache_location(remote_root, path, expected):
    actual = caching.path.remote_cache_location(remote_root, path)

    assert actual == expected
