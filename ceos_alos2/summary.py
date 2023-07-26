import re

from tlz.dicttoolz import merge, valmap
from tlz.functoolz import compose_left, curry, juxt
from tlz.itertoolz import first, groupby
from tlz.itertoolz import identity as passthrough
from tlz.itertoolz import second

from ceos_alos2.dicttoolz import keysplit

try:
    ExceptionGroup
except NameError:  # pragma: no cover
    from exceptiongroup import ExceptionGroup  # pragma: no cover

entry_re = re.compile(r'(?P<section>[A-Za-z]{3})_(?P<keyword>.*?)="(?P<value>.*?)"')


def parse_line(line):
    match = entry_re.fullmatch(line)
    if match is None:
        raise ValueError("invalid line")

    return match.groupdict()


def with_lineno(e, lineno):
    message = e.args[0]

    e.args = (f"line {lineno:02d}: {message}",) + e.args[1:]

    return e


def parse_summary(content):
    lines = content.splitlines()

    entries = []
    errors = {}
    for lineno, line in enumerate(lines):
        try:
            parsed = parse_line(line)
            entries.append(parsed)
        except ValueError as e:
            errors[lineno] = e

    if errors:
        new_errors = [with_lineno(error, lineno) for lineno, error in errors.items()]
        raise ExceptionGroup("failed to parse the summary", new_errors)

    merge_sections = compose_left(
        curry(groupby, lambda x: x["section"]),
        curry(
            valmap,
            compose_left(curry(map, lambda x: {x["keyword"]: x["value"]}), merge),
        ),
    )
    merged = merge_sections(entries)
    return process_sections(merged)


def categorize_filenames(filenames):
    filenames_ = list(filenames.values())
    return {
        "volume_directory": filenames_[0],
        "sar_leader": filenames_[1],
        "sar_imagery": filenames_[2:-1],
        "sar_trailer": filenames_[-1],
    }


def transform_product_info(section):
    file_info, remainder = keysplit(lambda x: "ProductFileName" in x, section)
    # ignore the file count
    _, filenames = keysplit(lambda x: x.startswith("Cnt"), file_info)
    categorized = categorize_filenames(filenames)

    shape_related, remainder = keysplit(
        lambda x: x.startswith(("NoOfPixels", "NoOfLines")), remainder
    )
    shapes_ = valmap(
        compose_left(
            curry(
                map,
                juxt(
                    compose_left(first, lambda x: first(x.split("_"))),
                    compose_left(second, int),
                ),
            ),
            dict,
        ),
        groupby(lambda it: second(first(it).split("_")), shape_related.items()),
    )
    shapes = valmap(lambda x: (x["NoOfLines"], x["NoOfPixels"]), shapes_)
    metadata = remainder

    return {
        "data_files": categorized,
        "shapes": shapes,
        **metadata,
    }


def process_sections(sections):
    transformers = {
        "Pdi": transform_product_info,
    }

    return {k: transformers.get(k, passthrough)(v) for k, v in sections.items()}
