import re

from tlz.dicttoolz import dissoc, valmap
from tlz.functoolz import compose_left, curry
from tlz.itertoolz import groupby

try:
    ExceptionGroup
except NameError:
    from exceptiongroup import ExceptionGroup

entry_re = re.compile(r'(?P<section>[A-Za-z]{3})_(?P<keyword>.*?)="(?P<value>.*?)"')


def parse_summary(content):
    def parse_lines(lines):
        for lineno, line in enumerate(lines):
            match = entry_re.fullmatch(line)
            if match is not None:
                yield match.groupdict()
            else:
                yield ValueError(f"line {lineno:02d}: invalid line")

    def extract_errors(entries):
        grouped = groupby(lambda x: isinstance(x, Exception), entries)

        return grouped.get(False, []), grouped.get(True, [])

    parse_all = compose_left(
        str.splitlines,
        parse_lines,
        extract_errors,
    )

    entries, errors = parse_all(content)
    if errors:
        raise ExceptionGroup("failed to parse the summary", errors)

    merge_sections = compose_left(
        curry(groupby, lambda x: x["section"]),
        curry(valmap, compose_left(curry(map, lambda x: dissoc(x, "section")), list)),
    )
    return merge_sections(entries)
