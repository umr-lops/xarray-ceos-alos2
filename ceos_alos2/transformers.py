import datetime as dt

from tlz.dicttoolz import keyfilter


def normalize_datetime(string):
    return dt.datetime.strptime(string, "%Y%m%d%H%M%S%f").isoformat()


def remove_spares(mapping):
    return keyfilter(lambda k: not k.startswith("spare") or not k[5:].isdigit(), mapping)
