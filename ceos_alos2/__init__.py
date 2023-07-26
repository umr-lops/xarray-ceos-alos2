from importlib.metadata import version

from ceos_alos2.xarray import open_alos2  # noqa: F401

try:
    __version__ = version("alos2")
except Exception:
    __version__ = "999"
