import datetime as dt

from tlz.dicttoolz import keyfilter, valmap
from tlz.itertoolz import groupby, second

from ceos_alos2.hierarchy import Group, Variable


def normalize_datetime(string):
    return dt.datetime.strptime(string, "%Y%m%d%H%M%S%f").isoformat()


def remove_spares(mapping):
    return keyfilter(lambda k: not k.startswith("spare") or not k[5:].isdigit(), mapping)


def item_type(item):
    value = second(item)
    if isinstance(value, tuple) and not isinstance(value[0], dict):
        return "variable"
    elif isinstance(value, dict) or (isinstance(value, tuple) and isinstance(value[0], dict)):
        return "group"
    else:
        return "attribute"


def as_variable(value):
    data, attrs = value

    return Variable((), data, attrs)


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
