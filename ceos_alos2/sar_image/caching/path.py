import hashlib

import platformdirs

project_name = "xarray-ceos-alos2"
cache_root = platformdirs.user_cache_path(project_name)


def hashsum(data, algorithm="sha256"):
    m = hashlib.new(algorithm)
    m.update(data.encode())
    return m.hexdigest()


def local_cache_location(remote_root, path):
    _, fname = f"/{path}".rsplit("/", 1)
    cache_name = f"{fname}.index"

    return cache_root / hashsum(remote_root) / cache_name


def remote_cache_location(remote_root, path):
    return f"{path}.index"
