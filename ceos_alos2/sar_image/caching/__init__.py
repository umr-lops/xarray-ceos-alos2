import json

from ceos_alos2.sar_image.caching.decoders import decode_hierarchy, postprocess
from ceos_alos2.sar_image.caching.encoders import encode_hierarchy, preprocess
from ceos_alos2.sar_image.caching.path import (
    local_cache_location,
    remote_cache_location,
)


class CachingError(FileNotFoundError):
    pass


def encode(obj):
    encoded = encode_hierarchy(obj)

    return json.dumps(preprocess(encoded))


def decode(cache, records_per_chunk):
    partially_decoded = json.loads(cache, object_hook=postprocess)

    return decode_hierarchy(partially_decoded, records_per_chunk=records_per_chunk)


def read_cache(mapper, path, records_per_chunk):
    remote = remote_cache_location(mapper.root, path)
    local = local_cache_location(mapper.root, path)

    if local.is_file():
        return decode(local.read_text(), records_per_chunk=records_per_chunk)

    if remote in mapper:
        return decode(mapper[remote].decode(), records_per_chunk=records_per_chunk)

    raise CachingError(f"no cache found for {path}")


def create_cache(mapper, path, data):
    local = local_cache_location(mapper.root, path)

    # ensure the directory exists
    local.parent.mkdir(exist_ok=True, parents=True)

    encoded = encode(data)

    local.write_text(encoded)
