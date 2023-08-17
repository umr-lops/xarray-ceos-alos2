from tlz.dicttoolz import assoc_in, keyfilter
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


def move_items(instructions, mapping):
    new = mapping
    for source, dest in instructions.items():
        if source not in mapping:
            continue

        new = assoc_in(new, dest, mapping[source])

    return dissoc(list(instructions), new)
