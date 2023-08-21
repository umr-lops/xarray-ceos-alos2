import datetime as dt

from tlz.dicttoolz import keyfilter, merge_with, valmap
from tlz.functoolz import curry, pipe
from tlz.itertoolz import groupby, second

from ceos_alos2.hierarchy import Group, Variable


def normalize_datetime(string):
    return dt.datetime.strptime(string, "%Y%m%d%H%M%S%f").isoformat()


def remove_spares(mapping):
    def predicate(k):
        if not k.startswith(("spare", "blanks")):
            return True

        k_ = k.removeprefix("spare").removeprefix("blanks")

        return k_ and not k_.isdigit()

    def _recursive(value):
        if isinstance(value, list):
            return list(map(remove_spares, value))
        elif isinstance(value, dict):
            filtered = keyfilter(predicate, value)

            return valmap(_recursive, filtered)
        else:
            return value

    return _recursive(mapping)


def item_type(item):
    value = second(item)
    if (isinstance(value, tuple) and not isinstance(value[0], dict)) or isinstance(value, list):
        return "variable"
    elif isinstance(value, dict) or (isinstance(value, tuple) and isinstance(value[0], dict)):
        return "group"
    else:
        return "attribute"


def transform_nested(mapping):
    def _transform(value):
        if not isinstance(value, list) or not value or not isinstance(value[0], dict):
            return value

        return merge_with(list, *value)

    return pipe(
        mapping,
        curry(_transform),
        curry(valmap, _transform),
    )


def separate_attrs(data):
    if not isinstance(data, list) or not data or not isinstance(data[0], tuple):
        return data, {}

    values, metadata_ = zip(*data)
    metadata = metadata_[0]

    return list(values), metadata


def as_variable(value):
    if len(value) == 2:
        data, attrs = value
        dims = ()
    else:
        dims, data, attrs = value

    return Variable(dims, data, attrs)


def as_group(mapping):
    if isinstance(mapping, tuple):
        mapping, additional_attrs = mapping
    else:
        additional_attrs = {}

    grouped = valmap(dict, dict(groupby(item_type, mapping.items())))

    attrs = grouped.get("attribute", {})
    variables = valmap(as_variable, grouped.get("variable", {}))
    groups = valmap(as_group, grouped.get("group", {}))

    return Group(path=None, url=None, data=variables | groups, attrs=attrs | additional_attrs)
