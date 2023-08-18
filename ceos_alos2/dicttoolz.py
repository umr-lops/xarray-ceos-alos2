import copy

from tlz.dicttoolz import assoc as assoc_
from tlz.dicttoolz import assoc_in, get_in, keyfilter
from tlz.itertoolz import concat, groupby
from tlz.itertoolz import identity as passthrough

from ceos_alos2.utils import unique

sentinel = object()


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


def assoc(key, value, d):
    return assoc_(d, key, value)


def dissoc(keys, d):
    return keyfilter(lambda k: k not in keys, d)


def zip_default(*mappings, default=None):
    all_keys = unique(concat(map(list, mappings)))

    return {k: [m.get(k, default) for m in mappings] for k in all_keys}


def apply_to_items(funcs, mapping, default=passthrough):
    return {k: funcs.get(k, default)(v) for k, v in mapping.items()}


def copy_items(instructions, mapping):
    new = mapping
    for dest, source in instructions.items():
        value = get_in(source, mapping, default=sentinel)
        if value is sentinel:
            continue

        new = assoc_in(new, list(dest), value)

    return new


def move_items(instructions, mapping):
    copied = copy.deepcopy(copy_items(instructions, mapping))

    for *head, tail in instructions.values():
        subset = get_in(list(head), copied, default=sentinel)
        if subset is sentinel:
            continue
        subset.pop(tail, None)

    return copied
