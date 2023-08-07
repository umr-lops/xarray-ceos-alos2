import posixpath
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
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

    def __eq__(self, other):
        if not isinstance(other, Variable):
            return False

        if self.dims != other.dims:
            return False
        if type(self.data) is not type(other.data):
            return False
        if self.attrs != other.attrs:
            return False

        if isinstance(self.data, Array):
            return self.data == other.data
        else:
            return np.all(self.data == other.data)

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
            return {}

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
        if self.path is None:
            self.path = "/"  # or raise

        for name, item in self.data.items():
            if not isinstance(item, Group):
                continue

            item.path = posixpath.join(self.path, name)

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

        _, name = self.path.rsplit("/", 1)
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

    def __eq__(self, other):
        if not isinstance(other, Group):
            return False

        if self.name != other.name:
            return False
        if self.url != other.url:
            return False
        if list(self.variables) != list(other.variables):
            # same variable names
            return False
        if list(self.groups) != list(other.groups):
            return False
        if self.attrs != other.attrs:
            return False

        for name, var in self.variables.items():
            if var.identical(other.data[name]):
                continue

            return False

        for name, group in self.groups.items():
            if group.identical(other.data[name]):
                continue

            return False

        return True
