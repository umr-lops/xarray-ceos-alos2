import fsspec
from fsspec.implementations.dirfs import DirFileSystem
from tlz.functoolz import curry

from ceos_alos2 import sar_image
from ceos_alos2.array import Array
from ceos_alos2.hierarchy import Group, Variable

# from ceos_alos2.sar_leader import sar_leader_record
from ceos_alos2.summary import parse_summary

# from ceos_alos2.utils import to_dict

# from ceos_alos2.volume_directory import volume_directory_record


def read_summary(mapper, path):
    try:
        bytes_ = mapper[path]
    except FileNotFoundError as e:
        raise OSError(
            f"Cannot find the summary file (`{path}`)."
            f" Make sure the dataset at {mapper.root} is complete and in the JAXA CEOS format."
        ) from e

    return parse_summary(bytes_.decode())


def read_image(mapper, path, chunks, *, use_cache=True, create_cache=False):
    dims = ["rows", "columns"]
    chunksizes = tuple(chunks.get(dim, -1) for dim in dims)

    try:
        fs = mapper.dirfs
    except AttributeError:
        fs = DirFileSystem(fs=mapper.fs, path=mapper.root)

    try:
        if not use_cache:
            # don't use the cache
            raise sar_image.CachingError()
        metadata = sar_image.read_cache(mapper, path)
    except sar_image.CachingError:
        with fs.open(path, mode="rb") as f:
            metadata = sar_image.read_metadata(f, chunksizes[0])
        if create_cache:
            sar_image.create_cache(mapper, path, metadata)

    parser = curry(sar_image.parse_data, type_code=metadata["type_code"])

    dtype = sar_image.dtypes.get(metadata["type_code"])
    if dtype is None:
        raise ValueError(f"unknown type code: {metadata['type_code']}")

    image_data = Array(
        fs=fs,
        url=path,
        byte_ranges=metadata["byte_ranges"],
        shape=metadata["shape"],
        dtype=dtype,
        parse_bytes=parser,
        chunks=chunksizes,
    )

    # transform metadata:
    # - group attrs
    # - coords
    # - image variable attrs
    image_variable = (dims, image_data, {})

    raw_variables = metadata["variables"] | {"data": image_variable}
    variables = {name: Variable(*var) for name, var in raw_variables.items()}

    group_name = sar_image.filename_to_groupname(path)

    group_attrs = metadata["attrs"]

    return Group(path=group_name, data=variables, attrs=group_attrs, url=None)


def open(path, chunks=None, *, storage_options={}, create_cache=False, use_cache=True):
    mapper = fsspec.get_mapper(path, **storage_options)

    # the default is to read 1024 records at once
    if chunks is None:
        chunks = {"rows": 1024}

    # read summary
    # TODO: split into metadata for the reader and human-readable metadata
    summary = read_summary(mapper, "summary.txt")

    filenames = summary["Pdi"]["data_files"]

    # read volume directory
    # read sar leader
    # read actual imagery
    imagery_groups = [
        read_image(mapper, path, chunks, create_cache=create_cache, use_cache=use_cache)
        for path in filenames["sar_imagery"]
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
