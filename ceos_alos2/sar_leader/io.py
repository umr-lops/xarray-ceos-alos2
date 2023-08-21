from ceos_alos2.sar_leader.metadata import transform_metadata
from ceos_alos2.sar_leader.structure import sar_leader_record
from ceos_alos2.utils import to_dict


def parse_data(data):
    return to_dict(sar_leader_record.parse(data))


def open_sar_leader(mapper, path):
    try:
        data = mapper[path]
    except KeyError as e:
        raise FileNotFoundError(f"Cannot open {path}") from e

    metadata = parse_data(data)

    return transform_metadata(metadata)
