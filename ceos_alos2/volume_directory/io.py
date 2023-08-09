from ceos_alos2.utils import to_dict
from ceos_alos2.volume_directory.metadata import transform_record
from ceos_alos2.volume_directory.structure import volume_directory_record


def open_volume_directory(mapper, path):
    try:
        data = mapper[path]
    except KeyError as e:
        raise FileNotFoundError(f"Cannot open {path}") from e

    metadata = volume_directory_record.parse(data)

    return transform_record(to_dict(metadata))
