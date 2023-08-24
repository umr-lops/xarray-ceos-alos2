from ceos_alos2.array import Array
from ceos_alos2.decoders import decode_filename
from ceos_alos2.hierarchy import Variable
from ceos_alos2.sar_image import caching
from ceos_alos2.sar_image.caching import CachingError
from ceos_alos2.sar_image.io import read_metadata
from ceos_alos2.sar_image.metadata import transform_metadata


def filename_to_groupname(path):
    info = decode_filename(path)
    scan_number = f"scan{info['scan_number']}" if "scan_number" in info else None
    polarization = info.get("polarization")
    parts = [polarization, scan_number]
    return "_".join([_ for _ in parts if _])


def open_image(mapper, path, *, use_cache=True, create_cache=False, records_per_chunk=None):
    if use_cache:
        try:
            return caching.read_cache(mapper, path, records_per_chunk=records_per_chunk)
        except CachingError:
            pass

    try:
        fs = mapper.dirfs
    except AttributeError:
        from fsspec.implementations.dirfs import DirFileSystem

        fs = DirFileSystem(fs=mapper.fs, path=mapper.root)

    with fs.open(path, mode="rb") as f:
        header, metadata = read_metadata(f, records_per_chunk)

        group, array_metadata = transform_metadata(header, metadata)

    group["data"] = Variable(
        dims=["rows", "columns"],
        data=Array(fs=fs, path=path, records_per_chunk=records_per_chunk, **array_metadata),
        attrs={},
    )
    group.path = filename_to_groupname(path)

    if create_cache:
        caching.create_cache(mapper, path, group)

    return group
