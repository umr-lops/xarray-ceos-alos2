import re

from tlz.dicttoolz import dissoc, keyfilter, keymap, merge, valmap
from tlz.functoolz import compose_left, curry
from tlz.functoolz import identity as passthrough
from tlz.functoolz import pipe
from tlz.itertoolz import first, get, groupby, second

from ceos_alos2 import decoders
from ceos_alos2.dicttoolz import apply_to_items
from ceos_alos2.hierarchy import Group
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

    merged = pipe(
        entries,
        curry(groupby, curry(get, "section")),
        curry(
            valmap,
            compose_left(curry(map, lambda x: {x["keyword"]: x["value"]}), merge),
        ),
    )
    return keymap(str.lower, merged)


def categorize_filenames(mapping):
    filenames = list(mapping.values())
    volume_directory, leader, *imagery, trailer = filenames
    return {
        "volume_directory": volume_directory,
        "sar_leader": leader,
        "sar_imagery": imagery,
        "sar_trailer": trailer,
    }


def reformat_date(s):
    return f"{s[:4]}-{s[4:6]}-{s[6:]}"


def to_isoformat(s):
    date, time = s.split()
    return f"{reformat_date(date)}T{time}"


def transform_ordering_info(section):
    # TODO: figure out what this means or what it would be used for
    return Group(path=None, url=None, data={}, attrs=section)


def transform_scene_spec(section):
    transformers = {
        "SceneID": compose_left(
            decoders.decode_scene_id,
            curry(
                apply_to_items,
                {
                    "date": lambda d: d.isoformat().split("T")[0],
                    "scene_frame": int,
                    "orbit_accumulation": int,
                },
            ),
        ),
        "SceneShift": int,
    }
    attrs = remove_nesting_layer(apply_to_items(transformers, section))
    return Group(path=None, url=None, data={}, attrs=attrs)


def transform_product_spec(section):
    transformers = {
        "ProductID": decoders.decode_product_id,
        "ResamplingMethod": curry(decoders.lookup, decoders.resampling_methods),
        "UTM_ZoneNo": int,
        "MapDirection": passthrough,
        "OrbitDataPrecision": passthrough,
        "AttitudeDataPrecision": passthrough,
    }

    attrs = remove_nesting_layer(apply_to_items(transformers, section, default=float))
    return Group(path=None, url=None, data={}, attrs=attrs)


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
    attrs = {k: transformers[determine_type(k)](v) for k, v in section.items()}
    return Group(path=None, url=None, data={}, attrs=attrs)


def transform_product_info(section):
    def categorize_key(item):
        key, _ = item
        if "ProductFileName" in key:
            return "data_files"
        elif key.startswith(("NoOfPixels", "NoOfLines")):
            return "shapes"
        else:
            return "other"

    def transform_file_info(mapping):
        filenames = keyfilter(lambda k: not k.startswith("Cnt"), mapping)
        categorized = categorize_filenames(filenames)

        return Group(path="data_files", url=None, data={}, attrs=categorized)

    def transform_shape(mapping):
        split_keys = keymap(lambda k: tuple(k.split("_")), mapping)
        grouped = groupby(lambda it: second(it[0]), split_keys.items())
        shapes = valmap(
            compose_left(
                dict,
                curry(keymap, first),
                curry(get, ["NoOfPixels", "NoOfLines"]),
                curry(map, int),
                tuple,
            ),
            grouped,
        )

        return Group(path="shapes", url=None, data={}, attrs=shapes)

    def transform_other(mapping):
        transformers = {
            "ProductFormat": passthrough,
            "BitPixel": int,
            "ProductDataSize": float,
        }

        return apply_to_items(transformers, mapping)

    categorized = valmap(dict, groupby(categorize_key, section.items()))
    transformers = {
        "data_files": transform_file_info,
        "shapes": transform_shape,
        "other": transform_other,
    }
    groups = apply_to_items(transformers, categorized)
    return Group(
        path="product_info", url=None, data=dissoc(groups, "other"), attrs=groups.get("other", {})
    )


def transform_autocheck(section):
    attrs = valmap(lambda s: s or "N/A", section)

    return Group(path=None, url=None, data={}, attrs=attrs)


def transform_result_info(section):
    return Group(path=None, url=None, data={}, attrs=section)


def transform_label_info(section):
    transformers = {
        "ObservationDate": reformat_date,
        "ProcessFacility": curry(decoders.lookup, decoders.processing_facilities),
    }
    attrs = apply_to_items(transformers, section)
    return Group(path=None, url=None, data={}, attrs=attrs)


def transform_summary(summary):
    transformers = {
        "odi": transform_ordering_info,
        "scs": transform_scene_spec,
        "pds": transform_product_spec,
        "img": transform_image_info,
        "pdi": transform_product_info,
        "ach": transform_autocheck,
        "rad": transform_result_info,
        "lbi": transform_label_info,
    }

    return pipe(
        summary,
        curry(apply_to_items, transformers),
        curry(rename, translations=section_names),
        curry(Group, "summary", None, attrs={}),
    )


def open_summary(mapper, path):
    try:
        bytes_ = mapper[path]
    except KeyError as e:
        raise OSError(
            f"Cannot find the summary file (`{path}`)."
            f" Make sure the dataset at {mapper.root} is complete and in the JAXA CEOS format."
        ) from e

    raw_summary = parse_summary(bytes_.decode())

    return transform_summary(raw_summary)
