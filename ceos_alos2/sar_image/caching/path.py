import hashlib
import pathlib

import platformdirs

project_name = "xarray-ceos-alos2"


def hashsum(data, algorithm="sha256"):
    m = hashlib.new(algorithm)
    m.update(data.encode())
    return m.hexdigest()


def local_cache_location(remote_root, path):
    subdirs, fname = f"/{path}".rsplit("/", 1)
    cache_name = f"{fname}.index"

    local_root = pathlib.Path(platformdirs.user_cache_dir(project_name))
    return local_root / hashsum(remote_root) / cache_name


def remote_cache_location(remote_root, path):
    return f"{path}.index"
