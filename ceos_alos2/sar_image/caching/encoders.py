import numpy as np
from tlz.dicttoolz import valmap

from ceos_alos2.array import Array
from ceos_alos2.hierarchy import Group, Variable


def encode_timedelta(obj):
    units, _ = np.datetime_data(obj.dtype)

    return obj.astype("int64").tolist(), {"units": units}


def encode_datetime(obj):
    units, _ = np.datetime_data(obj.dtype)
    reference = obj[0]

    encoding = {"reference": str(reference), "units": units}
    encoded = (obj - reference).astype("int64").tolist()

    return encoded, encoding


def encode_array(obj):
    if isinstance(obj, Array):
        return {
            "__type__": "backend_array",
            "root": obj.fs.path,
            "url": obj.url,
            "shape": obj.shape,
            "dtype": str(obj.dtype),
            "byte_ranges": obj.byte_ranges,
            "type_code": obj.type_code,
        }

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


def encode_variable(var):
    encoded_data = encode_array(var.data)

    return {
        "__type__": "variable",
        "dims": var.dims,
        "data": encoded_data,
        "attrs": var.attrs,
    }


def encode_group(group):
    def encode_entry(obj):
        if isinstance(obj, Group):
            return encode_group(obj)
        else:
            return encode_variable(obj)

    encoded_data = valmap(encode_entry, group.data)

    return {
        "__type__": "group",
        "url": group.url,
        "data": encoded_data,
        "path": group.path,
        "attrs": group.attrs,
    }


def encode_hierarchy(obj):
    if isinstance(obj, Group):
        return encode_group(obj)
    elif isinstance(obj, Variable):
        return encode_variable(obj)
    else:
        return obj


def preprocess(data):
    if isinstance(data, dict):
        return valmap(preprocess, data)
    elif isinstance(data, list):
        return list(map(preprocess, data))
    elif isinstance(data, tuple):
        return {"__type__": "tuple", "data": list(map(preprocess, data))}
    else:
        return data
