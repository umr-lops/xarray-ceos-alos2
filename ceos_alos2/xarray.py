import datatree
import numpy as np
import numpy.typing
import xarray as xr
from xarray.backends import BackendArray
from xarray.backends.locks import SerializableLock
from xarray.core import indexing

from ceos_alos2 import io
from ceos_alos2.array import Array


class LazilyIndexedWrapper(BackendArray):
    def __init__(self, array, lock):
        self.array = array
        self.lock = lock
        self.shape = array.shape
        self.dtype = array.dtype

    def __getitem__(self, key: indexing.ExplicitIndexer) -> np.typing.ArrayLike:
        return indexing.explicit_indexing_adapter(
            key,
            self.shape,
            indexing.IndexingSupport.BASIC,
            self._raw_indexing_method,
        )

    def _raw_indexing_method(self, key: tuple) -> np.typing.ArrayLike:
        with self.lock:
            return self.array[key]


def extract_encoding(var):
    chunks = var.chunks

    if all(c is None for c in chunks.values()):
        return {}

    normalized_chunks = {
        dim: chunksize if chunksize not in (None, -1) else var.sizes[dim]
        for dim, chunksize in chunks.items()
    }

    return {"preferred_chunksizes": normalized_chunks}


def to_variable(var):
    # only need a read lock, we don't support writing
    # TODO: do we even need the lock?
    if isinstance(var.data, Array):
        lock = SerializableLock()
        data = indexing.LazilyIndexedArray(LazilyIndexedWrapper(var.data, lock))
    else:
        data = var.data

    return xr.Variable(var.dims, data, var.attrs, encoding=extract_encoding(var))


def decode_coords(ds):
    coords = ds.attrs.pop("coordinates", [])

    return ds.set_coords(coords)


def to_dataset(group, chunks=None):
    variables = {name: to_variable(var) for name, var in group.variables.items()}
    backend_ds = xr.Dataset(variables, attrs=group.attrs).pipe(decode_coords)

    return xr.backends.api._dataset_from_backend_dataset(
        backend_ds,
        group.url,
        engine="ceos-alos2",
        chunks=chunks,
        overwrite_encoded_chunks=None,
        inline_array=True,
        chunked_array_type="dask",
        from_array_kwargs={},
        drop_variables=None,
        cache=chunks is None,
    )


def to_datatree(group, chunks=None):
    mapping = {"/": to_dataset(group, chunks=chunks)} | {
        path: to_dataset(subgroup, chunks=chunks) for path, subgroup in group.subtree
    }
    return datatree.DataTree.from_dict(mapping)


def open_alos2(path, chunks=None, storage_options={}, backend_options={}):
    root = io.open(path, storage_options=storage_options, **backend_options)

    return to_datatree(root, chunks=chunks)
