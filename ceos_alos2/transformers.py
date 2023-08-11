import datetime as dt


def normalize_datetime(string):
    return dt.datetime.strptime(string, "%Y%m%d%H%M%S%f").isoformat()
