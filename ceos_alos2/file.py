from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import fsspec
from fsspec.implementations.dirfs import DirFileSystem
from rich.console import Console
from tlz.dicttoolz import get_in, valfilter
from tlz.functoolz import curry

from ceos_alos2 import sar_image
from ceos_alos2.array import Array

# from ceos_alos2.sar_leader import sar_leader_record
from ceos_alos2.summary import parse_summary

# from ceos_alos2.utils import to_dict

# from ceos_alos2.volume_directory import volume_directory_record

console = Console()


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


class File:
    def read_image(self, fs, path):
        with fs.open(path, mode="rb") as f:
            header, metadata = sar_image.read_metadata(f, self.chunks[0])

        byte_ranges = [(m.data.start, m.data.stop) for m in metadata]
        type_code = sar_image.extract_format_type(header)
        parser = curry(sar_image.parse_data, type_code=type_code)

        shape = sar_image.extract_shape(header)
        dtype = sar_image.extract_dtype(header)

        image_data = Array(
            fs=fs,
            url=path,
            byte_ranges=byte_ranges,
            shape=shape,
            dtype=dtype,
            parse_bytes=parser,
            chunks=self.chunks,
        )

        # transform metadata:
        # - group attrs
        # - coords
        # - image variable attrs
        group_attrs = sar_image.extract_attrs(header)
        coords, var_attrs = sar_image.transform_metadata(metadata)
        image_variable = (["rows", "columns"], image_data, var_attrs)

        raw_variables = coords | {"data": image_variable}
        variables = {name: Variable(*var) for name, var in raw_variables.items()}

        return Group(path=None, data=variables, attrs=group_attrs)

    def __init__(self, url_or_dirfs, chunks=None, **options):
        if isinstance(url_or_dirfs, DirFileSystem):
            self.fs = url_or_dirfs
        elif isinstance(url_or_dirfs, str):
            fs, url = fsspec.core.url_to_fs(url_or_dirfs)
            self.fs = DirFileSystem(path=url, fs=fs)
        else:
            raise ValueError(f"unkown type: {url_or_dirfs}")

        if chunks is None:
            chunks = (1024, -1)
        self.chunks = chunks

        try:
            with self.fs.open("summary.txt", mode="r") as f:
                summary = parse_summary(f.read())
        except FileNotFoundError as e:
            raise OSError(
                "Cannot find the summary file (`summary.txt`)."
                f" Make sure the dataset at {url} is complete and in the JAXA CEOS format."
            ) from e

        fnames = summary["Pdi"]["data_files"]

        # try:
        #     with self.fs.open(fnames["volume_directory"], mode="rb") as f:
        #         parsed = volume_directory.volume_directory_record.parse(f.read())
        #         vol_attrs = volume_directory.extract_metadata(parsed)
        # except FileNotFoundError as e:
        #     raise OSError(
        #         f"Cannot find the volume directory file (`{fnames['volume_directory']}`)."
        #         f" Make sure the dataset at {url} is complete and in the JAXA CEOS format."
        #     )

        # try:
        #     with self.fs.open(fnames["sar_leader"], mode="rb") as f:
        #         sar_leader = sar_leader_record.parse(f.read())
        # except FileNotFoundError as e:
        #     raise OSError(
        #         f"Cannot find the sar leader file (`{fnames['sar_leader']}`)."
        #         f" Make sure the dataset at {url} is complete and in the JAXA CEOS format."
        #     )

        image_groups = {
            sar_image.filename_to_groupname(path): self.read_image(self.fs, path)
            for path in fnames["sar_imagery"]
        }

        self._groups = image_groups

        # try:
        #     with dirfs.open(fnames["sar_trailer"], mode="rb") as f:
        #         trailer_header, image_ranges = read_sar_trailer_metadata(f)
        # except FileNotFoundError as e:
        #     raise OSError(
        #         f"Cannot find the sar trailer file (`{fnames['sar_trailer']}`)."
        #         f" Make sure the dataset at {url} is complete and in the JAXA CEOS format."
        #     )

    def __getitem__(self, path):
        parts = path.lstrip("/").split("/")
        return get_in(parts, self._groups, no_default=True)

    @property
    def groups(self):
        return self._groups

    @property
    def filename(self):
        return self.fs.path
