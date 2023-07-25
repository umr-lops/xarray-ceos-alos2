from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from tlz.dicttoolz import valfilter

from ceos_alos2.array import Array


@dataclass(frozen=True)
class Variable:
    dims: str | list[str]
    data: Array
    attrs: dict[str, Any]

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
        return self.data.chunks


@dataclass(frozen=True)
class Group(Mapping):
    path: str
    data: dict[str, "Group | Variable"]
    attrs: dict[str, Any]

    def __getitem__(self, item):
        return self.data[item]

    @property
    def name(self):
        if "/" not in self.path:
            return self.path

        _, name = self.rsplit("/", 1)
        return name

    def __len__(self):
        return len(self.keys())

    def __iter__(self):
        yield from self.keys()

    @property
    def groups(self):
        return valfilter(lambda el: isinstance(el, Group), self)

    @property
    def variables(self):
        return valfilter(lambda el: isinstance(el, Variable), self)
