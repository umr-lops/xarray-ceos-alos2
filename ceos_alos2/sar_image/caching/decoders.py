import fsspec
import numpy as np
from tlz.dicttoolz import valmap
from tlz.functoolz import curry

from ceos_alos2.array import Array
from ceos_alos2.hierarchy import Group, Variable


def postprocess(obj):
    if obj.get("__type__") == "tuple":
        return tuple(obj["data"])

    return obj


def decode_datetime(obj):
    encoding = obj["encoding"]
    reference = np.array(encoding["reference"], dtype=obj["dtype"])
    offsets = np.array(obj["data"], dtype=f"timedelta64[{encoding['units']}]")

    return reference + offsets


def decode_objects(obj):
    def default_decode(obj):
        return np.array(obj["data"], dtype=obj["dtype"])

    if obj.get("__type__") == "tuple":
        return tuple(obj["data"])
    elif obj.get("__type__") != "array":
        return obj

    dtype = np.dtype(obj["dtype"])
    decoders = {
        "M": decode_datetime,
    }
    decoder = decoders.get(dtype.kind, default_decode)

    return decoder(obj)


def decode_array(encoded, records_per_chunk):
    if not isinstance(encoded, dict):
        return encoded
    elif encoded.get("__type__") != "record_array":
        raise ValueError(f"unknown type: {encoded['__type__']}")

    mapper = fsspec.get_mapper(encoded["root"])
    try:
        fs = mapper.dirfs
    except AttributeError:
        from fsspec.implementations.dirfs import DirFileSystem

        fs = DirFileSystem(fs=mapper.fs, path=mapper.root)

    type_code = encoded["type_code"]
    url = encoded["url"]
    shape = encoded["shape"]
    dtype = encoded["dtype"]
    byte_ranges = encoded["byte_ranges"]
    return Array(
        fs=fs,
        url=url,
        byte_ranges=byte_ranges,
        shape=shape,
        dtype=dtype,
        type_code=type_code,
        records_per_chunk=records_per_chunk,
    )


def decode_hierarchy(encoded, records_per_chunk):
    type_ = encoded.get("__type__")

    decoders = {
        "group": decode_group,
        "variable": decode_variable,
    }
    decoder = decoders.get(type_)
    if decoder is None:
        return encoded

    return decoder(encoded, records_per_chunk=records_per_chunk)


def decode_group(encoded, records_per_chunk):
    if encoded.get("__type__") != "group":
        raise ValueError("not a group")

    data = valmap(curry(decode_hierarchy, records_per_chunk=records_per_chunk), encoded["data"])

    return Group(path=encoded["path"], url=encoded["url"], data=data, attrs=encoded["attrs"])


def decode_variable(encoded, records_per_chunk):
    if encoded.get("__type__") != "variable":
        raise ValueError("not a variable")

    data = decode_array(encoded["data"], records_per_chunk=records_per_chunk)

    return Variable(dims=encoded["dims"], data=data, attrs=encoded["attrs"])
