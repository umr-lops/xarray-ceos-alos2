import textwrap

from tlz.dicttoolz import merge_with, valfilter
from tlz.itertoolz import groupby

from ceos_alos2.hierarchy import Group, Variable

newline = "\n"


def dict_overlap(a, b):
    def status(k):
        if k in a and k in b:
            return "common"
        elif k not in a:
            return "missing_left"
        elif k not in b:
            return "missing_right"
        else:
            return "neither"

    all_keys = list(a | b)
    g = groupby(status, all_keys)

    missing_left = g.get("missing_left", [])
    common = g.get("common", [])
    missing_right = g.get("missing_right", [])

    return missing_left, common, missing_right


def diff_mapping_missing(keys, side):
    lines = [f"Missing {side}:"] + [f" - {k}" for k in keys]

    return newline.join(lines)


def diff_mapping_not_equal(left, right):
    merged = valfilter(lambda v: len(v) == 2, merge_with(list, left, right))

    lines = []
    for k, (vl, vr) in merged.items():
        if vl == vr:
            continue
        lines.append(f"{k}:")
        lines.append(f" L  {vl}")
        lines.append(f" R  {vr}")

    if not lines:
        return None

    formatted_lines = textwrap.indent(newline.join(lines), " ")

    return newline.join(["Differences:", formatted_lines])


def diff_mapping(a, b, name):
    missing_left, common, missing_right = dict_overlap(a, b)

    sections = []
    if missing_left:
        sections.append(diff_mapping_missing(missing_left, "left"))
    if missing_right:
        sections.append(diff_mapping_missing(missing_right, "right"))
    if common:
        sections.append(diff_mapping_not_equal(a, b))

    formatted_sections = textwrap.indent(newline.join(filter(None, sections)), "  ")

    return newline.join([f"{name}:", formatted_sections])


def diff_scalar(a, b, name):
    return textwrap.dedent(
        f"""\
        {name.title()}:
        L  {a}
        R  {b}
        """.rstrip()
    )


def diff_variable(a, b):
    pass


def diff_group(a, b):
    sections = []
    if a.path != b.path:
        sections.append(diff_scalar(a.path, b.path, name="Path"))
    if a.url != b.url:
        sections.append(diff_scalar(a.url, b.url, name="URL"))
    if a.attrs != b.attrs:
        sections.append(diff_mapping(a.attrs, b.attrs, name="Attributes"))

    formatted_sections = textwrap.indent("\n".join(sections), "  ")
    return newline.join(["Group objects are not equal:", formatted_sections])


def diff(a, b):
    if isinstance(a, Group):
        return diff_group(a, b)
    elif isinstance(a, Variable):
        return diff_variable(a, b)
    else:
        raise ValueError(f"unknown type: {type(a)}")


def assert_identical(a, b):
    # __tracebackhide__ = True
    # compare types
    assert type(a) is type(b), f"types mismatch: {type(a)} != {type(b)}"

    assert a == b, diff(a, b)
