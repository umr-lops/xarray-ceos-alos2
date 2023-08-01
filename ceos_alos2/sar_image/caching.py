import hashlib
import json
import pathlib

import numpy as np
import platformdirs
from tlz.dicttoolz import valmap


class CachingError(FileNotFoundError):
    pass


project_name = "xarray-ceos-alos2"


def hashsum(data, algorithm="sha256"):
    m = hashlib.new(algorithm)
    m.update(data.encode())
    return m.hexdigest()


def local_cache_location(remote_root, path):
    subdirs, fname = path.rstrip("/", 1)
    cache_name = f"{fname}.index"

    local_root = pathlib.Path(platformdirs.user_cache_dir(project_name))
    return local_root / hashsum(remote_root) / cache_name


def remote_cache_location(remote_root, path):
    return f"{path}.index"


def encode_timedelta(obj):
    units, _ = np.datetime_data(obj.dtype)

    return obj.astype(int).tolist(), {"units": units}


def encode_datetime(obj):
    units, _ = np.datetime_data(obj.dtype)
    reference = obj[0]

    encoding = {"reference": str(reference), "units": units}
    encoded = (obj - reference).astype(int).tolist()

    return encoded, encoding


def encode_array(obj):
    def default_encode(obj):
        return obj.tolist(), {}

    encoders = {
        "m": encode_timedelta,
        "M": encode_datetime,
    }
    encoder = encoders.get(obj.dtype.kind, default_encode)
    encoded, encoding = encoder(obj)

    return {
        "__type__": "array",
        "dtype": str(obj.dtype),
        "data": encoded,
        "encoding": encoding,
    }


def decode_datetime(obj):
    encoding = obj["encoding"]
    reference = np.array(encoding["reference_date"], dtype=obj["dtype"])

    timedelta = np.array(obj["data"], dtype=f"timedelta64[{encoding['units']}]")

    return reference + timedelta


def decode_array(obj):
    def default_decode(obj):
        return np.array(obj["data"], dtype=obj["dtype"])

    type_ = obj.get("__type__")
    if type_ == "tuple":
        return tuple(obj["data"])
    elif type_ != "array":
        return obj

    dtype = np.dtype(obj["dtype"])

    decoders = {
        "M": decode_datetime,
    }
    decoder = decoders.get(dtype.kind, default_decode)
    decoded = decoder(obj)

    return decoded


class ArrayEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, tuple):
            return {"__type__": "tuple", "data": list(obj)}
        elif not isinstance(obj, np.ndarray):
            return super().default(obj)

        return encode_array(obj)


def preprocess(data):
    if isinstance(data, dict):
        return valmap(preprocess, data)
    elif isinstance(data, list):
        return list(map(preprocess, data))
    elif isinstance(data, tuple):
        return {"__type__": "tuple", "data": list(preprocess(data))}
    else:
        return data


def encode(data):
    return json.dumps(preprocess(data), cls=ArrayEncoder)


def decode(cache):
    return json.loads(cache, object_hook=decode_array)


def read_cache(mapper, path):
    remote = remote_cache_location(mapper.root, path)
    local = local_cache_location(mapper.root, path)

    if local.is_file():
        return decode(local.read_binary())

    if remote in mapper:
        return decode(mapper[remote])

    raise CachingError(f"no cache found for {path}")


def create_cache(mapper, path, data):
    local = local_cache_location(mapper.root, path)

    # ensure the directory exists
    local.parent.mkdir(exist_ok=True, parents=True)

    encoded = encode(data)
    local.write_text(encoded)
