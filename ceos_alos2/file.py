import fsspec
from fsspec.implementations.dirfs import DirFileSystem
from rich.console import Console
from tlz.functoolz import curry

from ceos_alos2 import sar_image
from ceos_alos2.array import Array
from ceos_alos2.hierarchy import Group, Variable

# from ceos_alos2.sar_leader import sar_leader_record
from ceos_alos2.summary import parse_summary

# from ceos_alos2.utils import to_dict

# from ceos_alos2.volume_directory import volume_directory_record

console = Console()


def read_summary(mapper, path):
    try:
        bytes_ = mapper[path]
    except FileNotFoundError as e:
        raise OSError(
            f"Cannot find the summary file (`{path}`)."
            f" Make sure the dataset at {mapper.root} is complete and in the JAXA CEOS format."
        ) from e

    return parse_summary(bytes_.decode())


def read_image(fs, path, chunks):
    with fs.open(path, mode="rb") as f:
        header, metadata = sar_image.read_metadata(f, chunks[0])

    byte_ranges = [(m.data.start, m.data.stop) for m in metadata]
    type_code = sar_image.extract_format_type(header)
    parser = curry(sar_image.parse_data, type_code=type_code)

    shape = sar_image.extract_shape(header)
    dtype = sar_image.extract_dtype(header)

    image_data = Array(
        fs=fs,
        url=path,
        byte_ranges=byte_ranges,
        shape=shape,
        dtype=dtype,
        parse_bytes=parser,
        chunks=chunks,
    )

    # transform metadata:
    # - group attrs
    # - coords
    # - image variable attrs
    group_attrs = sar_image.extract_attrs(header)
    coords, var_attrs = sar_image.transform_metadata(metadata)
    image_variable = (["rows", "columns"], image_data, var_attrs)

    raw_variables = coords | {"data": image_variable}
    variables = {name: Variable(*var) for name, var in raw_variables.items()}

    group_name = sar_image.filename_to_groupname(path)

    return Group(path=group_name, data=variables, attrs=group_attrs, url=None)


def open(path, chunks=None, storage_options={}):
    mapper = fsspec.get_mapper(path, **storage_options)
    dirfs = DirFileSystem(fs=mapper.fs, path=mapper.root)

    # fill in fallback chunks
    if chunks is None:
        chunks = (1024, -1)

    # read summary
    # TODO: split into metadata for the reader and human-readable metadata
    summary = read_summary(mapper, "summary.txt")

    filenames = summary["Pdi"]["data_files"]

    # read volume directory
    # read sar leader
    # read actual imagery
    imagery_groups = [
        read_image(dirfs, path, chunks, **storage_options) for path in filenames["sar_imagery"]
    ]
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
