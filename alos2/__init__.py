from importlib.metadata import version

try:
    __version__ = version("alos2")
except Exception:
    __version__ = "999"
