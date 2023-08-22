import textwrap
from itertools import zip_longest

import numpy as np
from tlz.dicttoolz import merge_with, valfilter, valmap
from tlz.functoolz import curry, pipe
from tlz.itertoolz import cons, groupby

from ceos_alos2.array import Array
from ceos_alos2.dicttoolz import valsplit, zip_default
from ceos_alos2.hierarchy import Group, Variable

newline = "\n"


def dict_overlap(a, b):
    def status(k):
        if k not in a:
            return "missing_left"
        elif k not in b:
            return "missing_right"
        else:
            return "common"

    all_keys = list(a | b)
    g = groupby(status, all_keys)

    missing_left = g.get("missing_left", [])
    common = g.get("common", [])
    missing_right = g.get("missing_right", [])

    return missing_left, common, missing_right


def format_item(x):
    dtype = x.dtype
    if dtype.kind in {"m", "M"}:
        return str(x)

    return repr(x.item())


def format_array(arr):
    if isinstance(arr, Array):
        url = f"{arr.fs.fs.protocol}://" + arr.fs.sep.join([arr.fs.path, arr.url])
        lines = [
            f"Array(shape={arr.shape}, dtype={arr.dtype}, rpc={arr.records_per_chunk})",
            f"    url: {url}",
        ]

        return newline.join(lines)

    flattened = np.reshape(arr, (-1,))
    if flattened.size < 8:
        return f"{flattened.dtype}  " + " ".join(format_item(x) for x in flattened)
    else:
        head = flattened[:3]
        tail = flattened[-2:]

        return (
            f"{flattened.dtype}  "
            + " ".join(format_item(x) for x in head)
            + " ... "
            + " ".join(format_item(x) for x in tail)
        )


def format_variable(var):
    base_string = f"({', '.join(var.dims)})    {format_array(var.data)}"
    attrs = [f"    {k}: {v}" for k, v in var.attrs.items()]
    return newline.join(cons(base_string, attrs))


def format_inline(value):
    if isinstance(value, Variable):
        return format_variable(value)
    else:
        return str(value)


def diff_mapping_missing(keys, side):
    lines = [f"Missing {side}:"] + [f" - {k}" for k in keys]

    return newline.join(lines)


def diff_mapping_not_equal(left, right, name):
    merged = valfilter(lambda v: len(v) == 2, merge_with(list, left, right))

    lines = []
    for k, (vl, vr) in merged.items():
        if vl == vr:
            continue
        lines.append(f"  L {k}  {format_inline(vl)}")
        lines.append(f"  R {k}  {format_inline(vr)}")

    if not lines:
        return None

    formatted_lines = textwrap.indent(newline.join(lines), " ")

    return newline.join([f"Differing {name}:", formatted_lines])


def diff_mapping(a, b, name):
    missing_left, common, missing_right = dict_overlap(a, b)

    sections = []
    if missing_left:
        sections.append(diff_mapping_missing(missing_left, "left"))
    if missing_right:
        sections.append(diff_mapping_missing(missing_right, "right"))
    if common:
        sections.append(diff_mapping_not_equal(a, b, name=name.lower()))

    formatted_sections = textwrap.indent(newline.join(filter(None, sections)), "  ")

    return newline.join([f"{name.title()}:", formatted_sections])


def diff_scalar(a, b, name):
    return textwrap.dedent(
        f"""\
        Differing {name.title()}:
        L  {a}
        R  {b}
        """.rstrip()
    )


def compare_data(a, b):
    if type(a) is not type(b):
        return False

    if isinstance(a, Array):
        return a == b
    else:
        return a.shape == b.shape and np.all(a == b)


def diff_array(a, b):
    if not isinstance(a, Array):
        lines = [
            f"  L {format_array(a)}",
            f"  R {format_array(b)}",
        ]

        return newline.join(lines)

    sections = []
    if a.fs != b.fs:
        lines = ["Differing filesystem:"]
        # fs.protocol is always `dir`, so we have to check the wrapped fs
        if a.fs.fs.protocol != b.fs.fs.protocol:
            lines.append(f"  L protocol  {a.fs.fs.protocol}")
            lines.append(f"  R protocol  {b.fs.fs.protocol}")
        if a.fs.path != b.fs.path:
            lines.append(f"  L path  {a.fs.path}")
            lines.append(f"  R path  {b.fs.path}")
        sections.append(newline.join(lines))
    if a.url != b.url:
        lines = [
            "Differing urls:",
            f"  L url  {a.url}",
            f"  R url  {b.url}",
        ]
        sections.append(newline.join(lines))
    if a.byte_ranges != b.byte_ranges:
        lines = ["Differing byte ranges:"]
        for index, (range_a, range_b) in enumerate(zip_longest(a.byte_ranges, b.byte_ranges)):
            if range_a == range_b:
                continue
            lines.append(f"  L line {index + 1}  {range_a}")
            lines.append(f"  R line {index + 1}  {range_b}")
        sections.append(newline.join(lines))
    if a.shape != b.shape:
        lines = [
            "Differing shapes:",
            f"  {a.shape} != {b.shape}",
        ]
        sections.append(newline.join(lines))
    if a.dtype != b.dtype:
        lines = [
            "Differing dtypes:",
            f"  {a.dtype} != {b.dtype}",
        ]
        sections.append(newline.join(lines))
    if a.type_code != b.type_code:
        lines = [
            "Differing type code:",
            f"  L type_code  {a.type_code}",
            f"  R type_code  {b.type_code}",
        ]
        sections.append(newline.join(lines))
    if a.records_per_chunk != b.records_per_chunk:
        lines = [
            "Differing chunksizes:",
            f"  L records_per_chunk  {a.records_per_chunk}",
            f"  R records_per_chunk  {b.records_per_chunk}",
        ]
        sections.append(newline.join(lines))

    return newline.join(sections)


def diff_data(a, b, name):
    if type(a) is not type(b):
        lines = [
            f"Differing {name.lower()} types:",
            f"  L {type(a)}",
            f"  R {type(b)}",
        ]
        return newline.join(lines)

    diff = diff_array(a, b)
    return newline.join([f"Differing {name.lower()}:", textwrap.indent(diff, "  ")])


def format_sizes(sizes):
    return "(" + ", ".join(f"{k}: {s}" for k, s in sizes.items()) + ")"


def diff_variable(a, b):
    sections = []
    if a.dims != b.dims:
        lines = ["Differing dimensions:", f"  {format_sizes(a.sizes)} != {format_sizes(b.sizes)}"]
        sections.append(newline.join(lines))
    if not compare_data(a.data, b.data):
        sections.append(diff_data(a.data, b.data, name="Data"))
    if a.attrs != b.attrs:
        sections.append(diff_mapping(a.attrs, b.attrs, name="Attributes"))

    diff = newline.join(sections)
    return newline.join(
        ["Left and right Variable objects are not equal", textwrap.indent(diff, "  ")]
    )


def diff_group(a, b):
    sections = []
    if a.path != b.path:
        sections.append(diff_scalar(a.path, b.path, name="Path"))
    if a.url != b.url:
        sections.append(diff_scalar(a.url, b.url, name="URL"))
    if a.variables != b.variables:
        sections.append(diff_mapping(a.variables, b.variables, name="Variables"))
    if a.attrs != b.attrs:
        sections.append(diff_mapping(a.attrs, b.attrs, name="Attributes"))

    return newline.join(sections)


def diff_tree(a, b):
    tree_a = dict(a.subtree)
    tree_b = dict(b.subtree)

    sections = []

    missing, common = pipe(
        zip_default(tree_a, tree_b, default=None),
        curry(valmap, curry(map, lambda g: g.decouple() if g is not None else None)),
        curry(valmap, list),
        curry(valsplit, lambda groups: any(g is None for g in groups)),
    )
    if missing:
        lines = ["Differing tree structure:"]
        missing_left, missing_right = map(list, valsplit(lambda x: x[0] is None, missing))

        if missing_left:
            lines.append("  Missing left:")
            lines.extend(f"  - {k}" for k in missing_left)
        if missing_right:
            lines.append("  Missing right:")
            lines.extend(f"  - {k}" for k in missing_right)

        sections.append(newline.join(lines))
    if common:
        lines = []
        for path, (left, right) in common.items():
            if left == right:
                continue

            lines.append(f"  Group {path}:")
            lines.append(textwrap.indent(diff_group(left, right), "    "))
        if lines:
            sections.append(newline.join(cons("Differing groups:", lines)))

    diff = newline.join(sections)
    return newline.join(["Left and right Group objects are not equal", textwrap.indent(diff, "  ")])


def assert_identical(a, b):
    __tracebackhide__ = True
    # compare types
    assert type(a) is type(b), f"types mismatch: {type(a)} != {type(b)}"

    if not isinstance(a, (Group, Variable, Array)):
        raise TypeError("can only compare Group and Variable and Array objects")

    if isinstance(a, Group):
        assert a == b, diff_tree(a, b)
    elif isinstance(a, Variable):
        assert a == b, diff_variable(a, b)
    else:
        assert a == b, diff_array(a, b)
