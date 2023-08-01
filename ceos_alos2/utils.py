import datetime

from construct import EnumIntegerString
from construct.lib.containers import ListContainer


def to_dict(container):
    if isinstance(container, EnumIntegerString):
        return str(container)
    if isinstance(container, (int, float, str, bytes, complex, datetime.datetime)):
        return container
    elif isinstance(container, (list, tuple)):
        if isinstance(container, ListContainer):
            type_ = list
        else:
            type_ = type(container)
        return type_(to_dict(elem) for elem in container)

    return {name: to_dict(section) for name, section in container.items() if name != "_io"}
