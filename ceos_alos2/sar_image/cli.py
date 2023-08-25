import argparse
import pathlib
import sys

import fsspec

from ceos_alos2.sar_image import caching, open_image


def create_cache(image_path, cache_root, records_per_chunk):
    if not image_path.is_file():
        raise FileNotFoundError(f"Cannot find image file at given path: {image_path}")

    if cache_root is not None and not cache_root.is_dir():
        raise OSError(f"Cannot find the target cache root: {cache_root}")
    elif cache_root is None:
        cache_root = image_path.parent

    uri = image_path.parent.as_uri()
    mapper = fsspec.get_mapper(uri)
    path = image_path.name

    group = open_image(
        mapper, path, use_cache=False, create_cache=False, records_per_chunk=records_per_chunk
    )

    encoded = caching.encode(group)
    target = cache_root / f"{path}.index"

    target.write_text(encoded)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rpc",
        nargs="?",
        type=int,
        default=4096,
        help="records-per-chunk size used to create the cache files",
    )
    parser.add_argument(
        "image_path",
        type=pathlib.Path,
        help="image path to create a cache file for",
    )
    parser.add_argument(
        "cache_root",
        nargs="?",
        type=pathlib.Path,
        default=None,
        help=(
            "Root path to the new cache file. By default, it is created"
            " in the same directory as the image file."
        ),
    )
    args = parser.parse_args()

    try:
        create_cache(args.image_path, args.cache_root, records_per_chunk=args.rpc)
    except OSError as e:
        print(e.args[0], file=sys.stderr)
        sys.exit(1)
