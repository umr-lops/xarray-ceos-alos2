import fsspec
from tlz.functoolz import curry

from ceos_alos2 import sar_image
from ceos_alos2.hierarchy import Group

# from ceos_alos2.sar_leader import sar_leader_record
from ceos_alos2.summary import open_summary

# from ceos_alos2.volume_directory import volume_directory_record


def open(path, *, storage_options={}, create_cache=False, use_cache=True, records_per_chunk=1024):
    mapper = fsspec.get_mapper(path, **storage_options)

    # read summary
    # TODO: split into metadata for the reader and human-readable metadata
    summary = open_summary(mapper, "summary.txt")

    filenames = summary["product_information"]["data_files"].attrs

    # read volume directory
    # read sar leader
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

    subgroups = {"imagery": imagery}

    return Group(path="/", data=subgroups, url=mapper.root, attrs={})


# try:
#     with self.fs.open(fnames["volume_directory"], mode="rb") as f:
#         parsed = volume_directory.volume_directory_record.parse(f.read())
#         vol_attrs = volume_directory.extract_metadata(parsed)
# except FileNotFoundError as e:
#     raise OSError(
#         f"Cannot find the volume directory file (`{fnames['volume_directory']}`)."
#         f" Make sure the dataset at {url} is complete and in the JAXA CEOS format."
#     )

# try:
#     with self.fs.open(fnames["sar_leader"], mode="rb") as f:
#         sar_leader = sar_leader_record.parse(f.read())
# except FileNotFoundError as e:
#     raise OSError(
#         f"Cannot find the sar leader file (`{fnames['sar_leader']}`)."
#         f" Make sure the dataset at {url} is complete and in the JAXA CEOS format."
#     )

# image_groups = {
#     sar_image.filename_to_groupname(path): self.read_image(self.fs, path)
#     for path in fnames["sar_imagery"]
# }

# self._groups = image_groups

# try:
#     with dirfs.open(fnames["sar_trailer"], mode="rb") as f:
#         trailer_header, image_ranges = read_sar_trailer_metadata(f)
# except FileNotFoundError as e:
#     raise OSError(
#         f"Cannot find the sar trailer file (`{fnames['sar_trailer']}`)."
#         f" Make sure the dataset at {url} is complete and in the JAXA CEOS format."
#     )
