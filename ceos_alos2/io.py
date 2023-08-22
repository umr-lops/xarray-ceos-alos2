import fsspec
from tlz.functoolz import curry

from ceos_alos2 import sar_image
from ceos_alos2.hierarchy import Group
from ceos_alos2.sar_leader import open_sar_leader
from ceos_alos2.summary import open_summary
from ceos_alos2.volume_directory import open_volume_directory


def open(path, *, storage_options={}, create_cache=False, use_cache=True, records_per_chunk=1024):
    mapper = fsspec.get_mapper(path, **storage_options)

    # read summary
    summary = open_summary(mapper, "summary.txt")

    filenames = summary["product_information"]["data_files"].attrs

    # read volume directory
    volume_directory = open_volume_directory(mapper, filenames["volume_directory"])
    # read sar leader
    sar_leader = open_sar_leader(mapper, filenames["sar_leader"])
    # read actual imagery
    imagery_groups = list(
        map(
            curry(
                sar_image.open_image,
                mapper,
                records_per_chunk=records_per_chunk,
                create_cache=create_cache,
                use_cache=use_cache,
            ),
            filenames["sar_imagery"],
        )
    )
    imagery = Group(
        "/imagery", url=mapper.root, data={group.name: group for group in imagery_groups}, attrs={}
    )
    # read sar trailer
    subgroups = {"summary": summary, "metadata": sar_leader, "imagery": imagery}

    return Group(path="/", data=subgroups, url=mapper.root, attrs=volume_directory.attrs)
