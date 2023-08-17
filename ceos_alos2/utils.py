import datetime

from construct import EnumIntegerString
from construct.lib.containers import ListContainer
from tlz.dicttoolz import keymap


def unique(seq):
    return list(dict.fromkeys(seq))


def starcall(f, args, **kwargs):
    return f(*args, **kwargs)


def to_dict(container):
    if isinstance(container, EnumIntegerString):
        return str(container)
    if isinstance(container, (int, float, str, bytes, complex, datetime.datetime)):
        return container
    elif isinstance(container, (list, tuple)):
        if isinstance(container, ListContainer):
            type_ = list
        else:
            type_ = type(container)
        return type_(to_dict(elem) for elem in container)

    return {name: to_dict(section) for name, section in container.items() if name != "_io"}


def rename(mapping, translations):
    return keymap(lambda k: translations.get(k, k), mapping)


def remove_nesting_layer(mapping):
    def _remove(mapping):
        for key, value in mapping.items():
            if not isinstance(value, dict):
                yield key, value
                continue

            yield from value.items()

    return dict(_remove(mapping))


# vendored from `dask.utils.parse_bytes`
# https://github.com/dask/dask/blob/a68bbc814306c51177407d32067ee5a8aaa22181/dask/utils.py#L1455-L1528
byte_sizes = {
    "kB": 10**3,
    "MB": 10**6,
    "GB": 10**9,
    "TB": 10**12,
    "PB": 10**15,
    "KiB": 2**10,
    "MiB": 2**20,
    "GiB": 2**30,
    "TiB": 2**40,
    "PiB": 2**50,
    "B": 1,
    "": 1,
}
byte_sizes = {k.lower(): v for k, v in byte_sizes.items()}
byte_sizes.update({k[0]: v for k, v in byte_sizes.items() if k and "i" not in k})
byte_sizes.update({k[:-1]: v for k, v in byte_sizes.items() if k and "i" in k})


def parse_bytes(s: float | str) -> int:
    """Parse byte string to numbers

    >>> from dask.utils import parse_bytes
    >>> parse_bytes("100")
    100
    >>> parse_bytes("100 MB")
    100000000
    >>> parse_bytes("100M")
    100000000
    >>> parse_bytes("5kB")
    5000
    >>> parse_bytes("5.4 kB")
    5400
    >>> parse_bytes("1kiB")
    1024
    >>> parse_bytes("1e6")
    1000000
    >>> parse_bytes("1e6 kB")
    1000000000
    >>> parse_bytes("MB")
    1000000
    >>> parse_bytes(123)
    123
    >>> parse_bytes("5 foos")
    Traceback (most recent call last):
        ...
    ValueError: Could not interpret 'foos' as a byte unit
    """
    if isinstance(s, (int, float)):
        return int(s)
    s = s.replace(" ", "")
    if not any(char.isdigit() for char in s):
        s = "1" + s

    # this will never run until the end
    for i in range(len(s) - 1, -1, -1):
        if not s[i].isalpha():
            break
    index = i + 1

    prefix = s[:index]
    suffix = s[index:]

    try:
        n = float(prefix)
    except ValueError as e:
        raise ValueError("Could not interpret '%s' as a number" % prefix) from e

    try:
        multiplier = byte_sizes[suffix.lower()]
    except KeyError as e:
        raise ValueError("Could not interpret '%s' as a byte unit" % suffix) from e

    result = n * multiplier
    return int(result)
