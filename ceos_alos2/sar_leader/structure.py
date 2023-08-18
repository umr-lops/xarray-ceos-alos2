from construct import Struct, this

from ceos_alos2.sar_leader.attitude import attitude_record
from ceos_alos2.sar_leader.data_quality_summary import data_quality_summary_record
from ceos_alos2.sar_leader.dataset_summary import dataset_summary_record
from ceos_alos2.sar_leader.facility_related_data import (
    facility_related_data_5_record,
    facility_related_data_record,
)
from ceos_alos2.sar_leader.file_descriptor import file_descriptor_record
from ceos_alos2.sar_leader.map_projection import map_projection_record
from ceos_alos2.sar_leader.platform_position import platform_position_record
from ceos_alos2.sar_leader.radiometric_data import radiometric_data_record

sar_leader_record = Struct(
    "file_descriptor" / file_descriptor_record,
    "dataset_summary" / dataset_summary_record,
    "map_projection" / map_projection_record[this.file_descriptor.map_projection.number_of_records],
    "platform_position" / platform_position_record,
    "attitude" / attitude_record,
    "radiometric_data" / radiometric_data_record,
    "data_quality_summary" / data_quality_summary_record,
    "facility_related_data_1" / facility_related_data_record,
    "facility_related_data_2" / facility_related_data_record,
    "facility_related_data_3" / facility_related_data_record,
    "facility_related_data_4" / facility_related_data_record,
    "facility_related_data_5" / facility_related_data_5_record,
)
