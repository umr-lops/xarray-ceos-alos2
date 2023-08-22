import numpy as np
from tlz.dicttoolz import valfilter
from tlz.functoolz import compose_left, curry, pipe
from tlz.itertoolz import first

from ceos_alos2.dicttoolz import apply_to_items, dissoc
from ceos_alos2.hierarchy import Group, Variable
from ceos_alos2.sar_leader.attitude import transform_attitude
from ceos_alos2.sar_leader.data_quality_summary import transform_data_quality_summary
from ceos_alos2.sar_leader.dataset_summary import transform_dataset_summary
from ceos_alos2.sar_leader.facility_related_data import transform_record5
from ceos_alos2.sar_leader.map_projection import transform_map_projection
from ceos_alos2.sar_leader.platform_position import transform_platform_position
from ceos_alos2.sar_leader.radiometric_data import transform_radiometric_data
from ceos_alos2.utils import rename


def fix_attitude_time(group):
    if "platform_position" not in group or "attitude" not in group:
        return group

    reference_year = group["platform_position"].attrs["datetime_of_first_point"][:4]
    reference_date = np.array(f"{reference_year}-01-01", dtype="datetime64[ns]")

    for subgroup in group["attitude"].groups.values():
        time = subgroup.data["time"]
        new_data = reference_date + time.data
        subgroup.data["time"] = Variable(time.dims, new_data, time.attrs)

    return group


def transform_metadata(mapping):
    ignored = [
        "file_descriptor",
        "facility_related_data_1",
        "facility_related_data_2",
        "facility_related_data_3",
        "facility_related_data_4",
    ]
    transformers = {
        "dataset_summary": transform_dataset_summary,
        "map_projection": compose_left(first, transform_map_projection),
        "platform_position": transform_platform_position,
        "attitude": transform_attitude,
        "radiometric_data": transform_radiometric_data,
        "data_quality_summary": transform_data_quality_summary,
        "facility_related_data_5": transform_record5,
    }
    translations = {
        "facility_related_data_5": "transformations",
    }

    postprocessors = [fix_attitude_time]

    groups = pipe(
        mapping,
        curry(dissoc, ignored),
        curry(valfilter, bool),
        curry(apply_to_items, transformers),
        curry(rename, translations=translations),
        compose_left(*postprocessors),
    )

    return Group(path=None, url=None, data=groups, attrs={})
