import re

import dateutil.parser
from tlz.dicttoolz import merge
from tlz.functoolz import curry
from tlz.functoolz import identity as passthrough

from ceos_alos2.dicttoolz import valsplit

scene_id_re = re.compile(
    r"""(?x)
    (?P<mission_name>[A-Z0-9]{5})
    (?P<orbit_accumulation>[0-9]{5})
    (?P<scene_frame>[0-9]{4})
    -(?P<date>[0-9]{6})
    """
)
product_id_re = re.compile(
    r"""(?x)
    (?P<observation_mode>[A-Z]{3})
    (?P<observation_direction>[LR])
    (?P<processing_level>1\.0|1\.1|1\.5|3\.1)
    (?P<processing_option>[GR_])
    (?P<map_projection>[UL_])
    (?P<orbit_direction>[AD])
    """
)
scan_info_re = re.compile(
    r"""(?x)
    (?P<processing_method>[BF])
    (?P<scan_number>[0-9])
    """
)
fname_re = re.compile(
    r"""(?x)
    (?P<filetype>[A-Z]{3})
    (-(?P<polarization>[HV]{2}))?
    -(?P<scene_id>[A-Z0-9]{14}-[0-9]{6})
    -(?P<product_id>[A-Z0-9._]{10})
    (-(?P<scan_info>[BF][0-9]))?
    """
)

observation_modes = {
    "SBS": "spotlight mode",
    "UBS": "ultra-fine mode single polarization",
    "UBD": "ultra-fine mode dual polarization",
    "HBS": "high-sensitive mode single polarization",
    "HBD": "high-sensitive mode dual polarization",
    "HBQ": "high-sensitive mode full (quad.) polarimetry",
    "FBS": "fine mode single polarization",
    "FBD": "fine mode dual polarization",
    "FBQ": "fine mode full (quad.) polarimetry",
    "WBS": "ScanSAR nominal 14MHz mode single polarization",
    "WBD": "ScanSAR nominal 14MHz mode dual polarization",
    "WWS": "ScanSAR nominal 28MHz mode single polarization",
    "WWD": "ScanSAR nominal 28MHz mode dual polarization",
    "VBS": "ScanSAR wide mode single polarization",
    "VBD": "ScanSAR wide mode dual polarization",
}
observation_directions = {"L": "left looking", "R": "right looking"}
processing_levels = {
    "1.0": "level 1.0",
    "1.1": "level 1.1",
    "1.5": "level 1.5",
    "3.1": "level 3.1",
}
processing_options = {"G": "geo-code", "R": "geo-reference", "_": "not specified"}
map_projections = {"U": "UTM", "P": "PS", "M": "MER", "L": "LCC", "_": "not specified"}
orbit_directions = {"A": "ascending", "D": "descending"}
processing_methods = {"F": "full aperture_method", "B": "SPECAN method"}
resampling_methods = {"NN": "nearest-neighbor", "BL": "bilinear", "CC": "cubic convolution"}
processing_facilities = {
    "SCMO": "spacecraft control mission operation system",
    "EICS": "earth intelligence collection and sharing system",
}


def lookup(mapping, code):
    value = mapping.get(code)
    if value is None:
        raise ValueError(f"invalid code {code!r}")

    return value


translations = {
    "observation_mode": curry(lookup, observation_modes),
    "observation_direction": curry(lookup, observation_directions),
    "processing_level": curry(lookup, processing_levels),
    "processing_option": curry(lookup, processing_options),
    "map_projection": curry(lookup, map_projections),
    "orbit_direction": curry(lookup, orbit_directions),
    "date": curry(dateutil.parser.parse, yearfirst=True, dayfirst=False),
    "mission_name": passthrough,
    "orbit_accumulation": passthrough,
    "scene_frame": passthrough,
    "processing_method": curry(lookup, processing_methods),
    "scan_number": passthrough,
}


def decode_scene_id(scene_id):
    match = scene_id_re.match(scene_id)
    if match is None:
        raise ValueError(f"invalid scene id: {scene_id}")

    groups = match.groupdict()
    try:
        return {name: translations[name](value) for name, value in groups.items()}
    except ValueError as e:
        raise ValueError(f"invalid scene id: {scene_id}") from e


def decode_product_id(product_id):
    match = product_id_re.fullmatch(product_id)
    if match is None:
        raise ValueError(f"invalid product id: {product_id}")

    groups = match.groupdict()
    try:
        return {name: translations[name](value) for name, value in groups.items()}
    except ValueError as e:
        raise ValueError(f"invalid product id: {product_id}") from e


def decode_scan_info(scan_info):
    if scan_info is None:
        return {}

    match = scan_info_re.fullmatch(scan_info)
    if match is None:
        raise ValueError(f"invalid scan info: {scan_info}")

    groups = match.groupdict()
    return {name: translations[name](value) for name, value in groups.items()}


def decode_filename(fname):
    match = fname_re.fullmatch(fname)
    if match is None:
        raise ValueError(f"invalid file name: {fname}")

    parts = match.groupdict()
    translators = {
        "filetype": passthrough,
        "polarization": passthrough,
        "scene_id": decode_scene_id,
        "product_id": decode_product_id,
        "scan_info": decode_scan_info,
    }

    mapping = {name: translators[name](value) for name, value in parts.items()}
    scalars, mappings = valsplit(lambda x: not isinstance(x, dict), mapping)
    return scalars | merge(*mappings.values())
