from tlz.itertoolz import concat, groupby


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


def unique(seq):
    return list(dict.fromkeys(seq))


def zip_default(*mappings, default=None):
    all_keys = unique(concat(map(list, mappings)))

    return {k: [m.get(k, default) for m in mappings] for k in all_keys}
