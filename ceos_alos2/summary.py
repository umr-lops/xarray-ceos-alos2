import re

from tlz.dicttoolz import dissoc, keymap, merge, valmap
from tlz.functoolz import compose_left, curry, juxt, pipe
from tlz.itertoolz import first, groupby
from tlz.itertoolz import identity as passthrough
from tlz.itertoolz import second

from ceos_alos2 import decoders
from ceos_alos2.dicttoolz import keysplit
from ceos_alos2.utils import remove_nesting_layer, rename

try:
    ExceptionGroup
except NameError:  # pragma: no cover
    from exceptiongroup import ExceptionGroup  # pragma: no cover

entry_re = re.compile(r'(?P<section>[A-Za-z]{3})_(?P<keyword>.*?)="(?P<value>.*?)"')

section_names = {
    "odi": "ordering_information",
    "scs": "scene_specification",
    "pds": "product_specification",
    "img": "image_information",
    "pdi": "product_information",
    "ach": "autocheck",
    "rad": "result_information",
    "lbi": "label_information",
}


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
    return process_sections(keymap(str.lower, merged))


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

    count_fields = [name for name in file_info if name.startswith("Cnt")]
    filenames = dissoc(file_info, *count_fields)
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


def to_isoformat(s):
    date, time = s.split()
    return f"{date[:4]}-{date[4:6]}-{date[6:]}T{time}"


def transform_ordering_info(section):
    # TODO: figure out what this means or what it would be used for
    return section


def apply_to_items(funcs, mapping, default=passthrough):
    return {k: funcs.get(k, default)(v) for k, v in mapping.items()}


def transform_scene_spec(section):
    transformers = {
        "SceneID": compose_left(
            decoders.decode_scene_id,
            curry(
                apply_to_items,
                {"date": lambda d: d.isoformat(), "scene_frame": int, "orbit_accumulation": int},
            ),
        ),
        "SceneShift": int,
    }
    return remove_nesting_layer(apply_to_items(transformers, section))


def transform_image_info(section):
    def determine_type(key):
        if "DateTime" in key:
            return "datetime"
        else:
            return "float"

    transformers = {
        "datetime": to_isoformat,
        "float": float,
    }
    return {k: transformers[determine_type(k)](v) for k, v in section.items()}


def process_sections(sections):
    transformers = {
        "odi": transform_ordering_info,
        "scs": transform_scene_spec,
        "pdi": transform_product_info,
        "img": transform_image_info,
    }

    return apply_to_items(transformers, sections)


def transform_summary(summary):
    return pipe(
        summary,
        curry(rename, translations=section_names),
    )


def open_summary(mapper, path):
    try:
        bytes_ = mapper[path]
    except FileNotFoundError as e:
        raise OSError(
            f"Cannot find the summary file (`{path}`)."
            f" Make sure the dataset at {mapper.root} is complete and in the JAXA CEOS format."
        ) from e

    raw_summary = parse_summary(bytes_.decode())

    return transform_summary(raw_summary)
