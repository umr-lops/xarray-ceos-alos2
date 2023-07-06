import re

from tlz.dicttoolz import merge, valmap
from tlz.functoolz import compose_left, curry
from tlz.itertoolz import groupby

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
    return merge_sections(entries)
