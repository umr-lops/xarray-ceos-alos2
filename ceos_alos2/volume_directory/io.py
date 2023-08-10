from ceos_alos2.utils import to_dict
from ceos_alos2.volume_directory.metadata import transform_record
from ceos_alos2.volume_directory.structure import volume_directory_record


def parse_data(data):
    return to_dict(volume_directory_record.parse(data))


def open_volume_directory(mapper, path):
    try:
        data = mapper[path]
    except KeyError as e:
        raise FileNotFoundError(f"Cannot open {path}") from e

    metadata = parse_data(data)

    return transform_record(metadata)
