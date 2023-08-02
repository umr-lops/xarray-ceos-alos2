import posixpath
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from numpy.typing import ArrayLike
from tlz.dicttoolz import valfilter

from ceos_alos2.array import Array


@dataclass(frozen=True)
class Variable:
    dims: str | list[str]
    data: Array | ArrayLike
    attrs: dict[str, Any]

    def __post_init__(self):
        if isinstance(self.dims, str):
            # normalize, need the hack
            super().__setattr__("dims", [self.dims])

    @property
    def ndim(self):
        return self.data.ndim

    @property
    def shape(self):
        return self.data.shape

    @property
    def dtype(self):
        return self.data.dtype

    @property
    def chunks(self):
        if not isinstance(self.data, Array):
            return dict.fromkeys(self.dims)

        return dict(zip(self.dims, self.data.chunks))

    @property
    def sizes(self):
        return dict(zip(self.dims, self.data.shape))


@dataclass
class Group(Mapping):
    path: str | None
    url: str
    data: dict[str, "Group | Variable"]
    attrs: dict[str, Any]

    def __post_init__(self):
        if self.path is None and self.groups:
            self.path = "/"  # or raise

        for name, item in self.data.items():
            if not isinstance(item, Group):
                continue

            path = item.path
            if path is None:
                item.path = posixpath.join(self.path, name)
            elif not isinstance(path, str):
                raise TypeError("paths should be `str` or `None`")
            elif not posixpath.isabs(path):
                if "/" in path:
                    raise ValueError("relative paths cannot contain slashes")
                item.path = posixpath.join(self.path, path)
            elif posixpath.commonpath([self.path, path]) != self.path:
                raise ValueError(
                    "group paths need to be either `None`, relative paths,"
                    " or absolute paths below the parent group"
                )

            if item.url is None:
                item.url = self.url

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, item, value):
        self.data[item] = value

    @property
    def name(self):
        if "/" not in self.path:
            return self.path

        _, name = self.rsplit("/", 1)
        return name

    def __len__(self):
        return len(self.data.keys())

    def __iter__(self):
        yield from self.data.keys()

    @property
    def groups(self):
        return valfilter(lambda el: isinstance(el, Group), self.data)

    @property
    def variables(self):
        return valfilter(lambda el: isinstance(el, Variable), self.data)
