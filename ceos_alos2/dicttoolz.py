from tlz.dicttoolz import keyfilter
from tlz.itertoolz import concat, groupby
from tlz.itertoolz import identity as passthrough

from ceos_alos2.utils import unique


def itemsplit(predicate, d):
    groups = groupby(predicate, d.items())
    first = dict(groups.get(True, ()))
    second = dict(groups.get(False, ()))
    return first, second


def valsplit(predicate, d):
    wrapper = lambda item: predicate(item[1])
    return itemsplit(wrapper, d)


def keysplit(predicate, d):
    wrapper = lambda item: predicate(item[0])
    return itemsplit(wrapper, d)


def dissoc(keys, d):
    return keyfilter(lambda k: k not in keys, d)


def zip_default(*mappings, default=None):
    all_keys = unique(concat(map(list, mappings)))

    return {k: [m.get(k, default) for m in mappings] for k in all_keys}


def apply_to_items(funcs, mapping, default=passthrough):
    return {k: funcs.get(k, default)(v) for k, v in mapping.items()}
